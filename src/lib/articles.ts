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
    const line = lines[i];
    const titleMatch = line.match(/^-\s+(.*)$/);
    if (!titleMatch) {
      i++;
      continue;
    }
    const title = titleMatch[1].trim();
    if (!title) {
      console.warn("[articles] skip empty title at line", i + 1);
      i++;
      continue;
    }

    i++;
    const materialLines: string[] = [];
    while (i < lines.length) {
      const ml = lines[i];
      if (/^\s{2,}|\t/.test(ml)) {
        materialLines.push(ml.replace(/^(\s{2,}|\t)/, ""));
        i++;
      } else {
        break;
      }
    }

    const prompt =
      materialLines.length > 0
        ? [title, ...materialLines].join("\n")
        : title;

    const yearMatch = title.match(/\d{4}/);
    let id: string;
    if (yearMatch) {
      const year = yearMatch[0];
      yearCounters[year] = (yearCounters[year] ?? 0) + 1;
      id = `${year}-${yearCounters[year]}`;
    } else {
      idxFallback += 1;
      id = `idx-${idxFallback}`;
    }

    articles.push({ id, title, prompt });
  }

  return articles;
}

export const ARTICLES: Article[] = parseArticles(articlesRaw);
