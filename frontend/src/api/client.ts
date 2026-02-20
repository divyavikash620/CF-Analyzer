import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 5000,
});

export interface AnalysisResponse {
  tag_accuracy: Record<string, number>;
  rating_accuracy: Record<string, number>;
  average_solve_time: number;
  insights: string[];
}

export async function fetchAnalysis(handle: string): Promise<AnalysisResponse> {
  const response = await api.get<AnalysisResponse>(`/analysis/${handle}`);
  return response.data;
}
