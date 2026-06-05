export class AsyncLocalStorage<T> {
  getStore(): T | undefined {
    return undefined;
  }
  run(_store: T, callback: () => unknown): unknown {
    return callback();
  }
  enterWith(_store: T): void {
    // no-op
  }
}
