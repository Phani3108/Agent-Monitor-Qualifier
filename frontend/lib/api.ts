export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function fetchAuth(url: string, options?: RequestInit) {
  // Add authentication headers or logic here if needed
  return fetch(url, options);
}
