import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// 跟踪 getGraph(mode).stream 的调用,验证 mode 路由
const streamMock = vi.fn();

vi.mock("../../src/workflow/graph", () => {
  return {
    graph: { stream: () => (async function* () {})() },
    standardGraph: { stream: () => (async function* () {})() },
    gaokaoGraph: { stream: () => (async function* () {})() },
    getGraph: (mode: "standard" | "gaokao") => ({
      stream: (state: unknown) => {
        streamMock({ mode, state });
        return (async function* () {
          yield { check_relevance: { relevance: { score: 0.9, reason: "good" } } };
        })();
      },
    }),
  };
});

import { GradingPage } from "../../src/pages/GradingPage";

function renderGradingPage() {
  return render(
    <MemoryRouter>
      <GradingPage />
    </MemoryRouter>
  );
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("作文题目"), { target: { value: "我的题目" } });
  fireEvent.change(screen.getByLabelText("作文内容"), { target: { value: "我的作文内容" } });
  const form = document.querySelector("form.form-section")!;
  fireEvent.submit(form);
}

describe("GradingPage 配额集成", () => {
  beforeEach(() => {
    localStorage.clear();
    streamMock.mockClear();
  });

  it("配额未用尽时:点提交触发 graph.stream 并增加 used", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));

    renderGradingPage();

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());

    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 1 });
  });

  it("配额用尽时:即使提交表单,graph.stream 也不会被调用 (C1 修复)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 10 }));

    renderGradingPage();

    const btn = screen.getByRole("button", { name: /次数已用完/ }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);

    fillAndSubmit();

    await new Promise((r) => setTimeout(r, 50));

    expect(streamMock).not.toHaveBeenCalled();
    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 10 });
  });
});

describe("GradingPage 模式集成", () => {
  beforeEach(() => {
    localStorage.clear();
    streamMock.mockClear();
  });

  it("默认 mode = gaokao", () => {
    renderGradingPage();
    const gaokaoBtn = screen.getByRole("radio", { name: /高考模式/ }) as HTMLButtonElement;
    expect(gaokaoBtn.getAttribute("aria-checked")).toBe("true");
  });

  it("点「标准模式」后下次 run 调用 standardGraph (getGraph 收到 standard)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));
    renderGradingPage();

    fireEvent.click(screen.getByRole("radio", { name: /标准模式/ }));

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());
    const call = streamMock.mock.calls[0][0];
    expect(call.mode).toBe("standard");
  });

  it("高考模式下 run 调用 getGraph(gaokao)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 0 }));
    renderGradingPage();

    fillAndSubmit();

    await waitFor(() => expect(streamMock).toHaveBeenCalled());
    const call = streamMock.mock.calls[0][0];
    expect(call.mode).toBe("gaokao");
  });

  it("模式选择写入 localStorage", () => {
    renderGradingPage();

    fireEvent.click(screen.getByRole("radio", { name: /标准模式/ }));

    expect(localStorage.getItem("grading-mode-v1")).toBe(JSON.stringify("standard"));
  });

  it("已保存的 mode 加载时高亮对应按钮", () => {
    localStorage.setItem("grading-mode-v1", JSON.stringify("standard"));
    renderGradingPage();

    const standardBtn = screen.getByRole("radio", { name: /标准模式/ }) as HTMLButtonElement;
    const gaokaoBtn = screen.getByRole("radio", { name: /高考模式/ }) as HTMLButtonElement;
    expect(standardBtn.getAttribute("aria-checked")).toBe("true");
    expect(gaokaoBtn.getAttribute("aria-checked")).toBe("false");
  });
});
