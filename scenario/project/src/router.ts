import type { IncomingMessage, ServerResponse } from 'node:http';
import { HttpError, sendError } from './lib/http.ts';

export interface Ctx {
  req: IncomingMessage;
  res: ServerResponse;
  params: Record<string, string>;
  query: URLSearchParams;
}

export type Handler = (ctx: Ctx) => unknown;

interface Route {
  method: string;
  parts: string[];
  handler: Handler;
}

function split(path: string): string[] {
  return path.split('/').filter(Boolean);
}

function match(pattern: string[], parts: string[]): Record<string, string> | null {
  if (pattern.length !== parts.length) return null;
  const params: Record<string, string> = {};
  for (let i = 0; i < pattern.length; i++) {
    const p = pattern[i];
    if (p.startsWith(':')) params[p.slice(1)] = decodeURIComponent(parts[i]);
    else if (p !== parts[i]) return null;
  }
  return params;
}

/** Minimal router: static segments and `:param` segments, first match wins. */
export class Router {
  private routes: Route[] = [];

  add(method: string, pattern: string, handler: Handler): this {
    this.routes.push({ method, parts: split(pattern), handler });
    return this;
  }

  get(pattern: string, handler: Handler): this {
    return this.add('GET', pattern, handler);
  }

  post(pattern: string, handler: Handler): this {
    return this.add('POST', pattern, handler);
  }

  async handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const url = new URL(req.url ?? '/', 'http://localhost');
    const parts = split(url.pathname);
    try {
      let methodMismatch = false;
      for (const route of this.routes) {
        const params = match(route.parts, parts);
        if (!params) continue;
        if (route.method !== req.method) {
          methodMismatch = true;
          continue;
        }
        await route.handler({ req, res, params, query: url.searchParams });
        return;
      }
      throw methodMismatch
        ? new HttpError(405, 'METHOD_NOT_ALLOWED', 'Method not allowed')
        : new HttpError(404, 'NOT_FOUND', 'Route not found');
    } catch (err) {
      sendError(res, err);
    }
  }
}
