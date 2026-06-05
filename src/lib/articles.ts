import articlesRaw from "../data/articles.md?raw";

export type Article = {
  id: string;
  title: string;
  prompt: string;
};

export function parseArticles(raw: string): Article[] {
  if (typeof raw !== "string") return [];

  const lines = raw.split(/\r?\n/);
  const articles: Article[] = [];
  const yearCounters: Record<string, number> = {};
  let idxFallback = 0;

  let i = 0;
  while (i < lines.length) {
    const title = readTitle(lines[i]);
    if (title === null) {
      i++;
      continue;
    }
    if (title === "") {
      console.warn("[articles] 跳过空标题（行", i + 1, "）");
      i++;
      continue;
    }

    i++;
    const { materials, consumed } = collectMaterialLines(lines, i);
    i += consumed;

    const prompt = materials.length > 0 ? [title, ...materials].join("\n") : title;
    articles.push({ id: makeId(title, yearCounters, () => ++idxFallback), title, prompt });
  }

  return articles;
}

function readTitle(line: string): string | null {
  const m = line.match(/^-\s+(.*)$/);
  if (!m) return null;
  return m[1].trim();
}

function collectMaterialLines(lines: string[], start: number): { materials: string[]; consumed: number } {
  const materials: string[] = [];
  let i = start;
  while (i < lines.length && /^\s{2,}|\t/.test(lines[i])) {
    materials.push(lines[i].replace(/^(\s{2,}|\t)/, ""));
    i++;
  }
  return { materials, consumed: i - start };
}

function makeId(title: string, yearCounters: Record<string, number>, nextIdx: () => number): string {
  const ym = title.match(/\d{4}/);
  if (!ym) return `idx-${nextIdx()}`;
  const year = ym[0];
  yearCounters[year] = (yearCounters[year] ?? 0) + 1;
  return `${year}-${yearCounters[year]}`;
}

export const ARTICLES: Article[] = parseArticles(articlesRaw);
