import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// 跟踪 graph.stream 的调用 — 替代直接断言 run()
const streamMock = vi.fn();

vi.mock("../../src/workflow/graph", () => {
  return {
    graph: {
      stream: (state: unknown) => {
        streamMock(state);
        return (async function* () {
          yield { check_relevance: { relevance: { score: 0.9, reason: "good" } } };
        })();
      },
    },
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
  // 直接 fire form submit — 模拟用户按 Enter 键绕过 disabled 按钮的场景
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

    // 配额已自增
    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 1 });
  });

  it("配额用尽时:即使提交表单,graph.stream 也不会被调用 (C1 修复)", async () => {
    localStorage.setItem("grading-quota-v1", JSON.stringify({ used: 10 }));

    renderGradingPage();

    // 提交按钮被 disabled 且文案已切到「次数已用完」
    const btn = screen.getByRole("button", { name: /次数已用完/ }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);

    // 模拟用户按 Enter 键 — 提交事件绕过 disabled 按钮,直接打到 form.onSubmit
    fillAndSubmit();

    // 等一拍让任何潜在异步逻辑执行
    await new Promise((r) => setTimeout(r, 50));

    // C1 核心断言:run() 必须没被调用,配额也没有增加
    expect(streamMock).not.toHaveBeenCalled();
    expect(JSON.parse(localStorage.getItem("grading-quota-v1") ?? "{}")).toEqual({ used: 10 });
  });
});
