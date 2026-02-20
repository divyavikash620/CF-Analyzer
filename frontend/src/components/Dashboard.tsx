import { useRef, useState } from "react";
import axios from "axios";

import type { AnalysisResponse } from "../api/client";
import Insights from "./Insights";
import RatingStats from "./RatingStats";
import TagStats from "./TagStats";

interface DashboardError {
  title: string;
  message: string;
}

function Dashboard() {
  const [handle, setHandle] = useState<string>("");
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<DashboardError | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef<number>(0);

  const onAnalyze = async (): Promise<void> => {
    const trimmedHandle = handle.trim();
    if (!trimmedHandle) {
      setError({
        title: "Invalid input",
        message: "Please enter a handle.",
      });
      setData(null);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await axios.get<AnalysisResponse>(
        `${import.meta.env.VITE_API_URL}/analysis/${encodeURIComponent(trimmedHandle)}`,
        { signal: controller.signal, timeout: 5000 },
      );
      if (requestId !== requestIdRef.current || controller.signal.aborted) {
        return;
      }
      const result = response.data;
      setData(result);
    } catch (err: unknown) {
      if (controller.signal.aborted || requestId !== requestIdRef.current) {
        return;
      }

      if (axios.isAxiosError(err)) {
        setError({
          title: "Request failed",
          message: err.response?.data?.detail ?? err.message ?? "Failed to fetch analysis.",
        });
      } else {
        setError({
          title: "Unexpected error",
          message: err instanceof Error ? err.message : "Failed to fetch analysis.",
        });
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  };

  return (
    <div
      style={{
        maxWidth: "760px",
        margin: "40px auto",
        padding: "20px",
        fontFamily: "sans-serif",
        lineHeight: 1.4,
      }}
    >
      <h1 style={{ marginBottom: "16px" }}>CP Analyser Dashboard</h1>

      <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
        <input
          type="text"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          placeholder="Enter Codeforces handle"
          style={{ flex: 1, padding: "8px" }}
        />
        <button type="button" onClick={onAnalyze} disabled={loading} style={{ padding: "8px 12px", minWidth: "88px" }}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {loading && <p style={{ margin: "8px 0 16px" }}>Loading analysis...</p>}
      {error && (
        <div
          style={{
            marginTop: "8px",
            marginBottom: "16px",
            padding: "10px 12px",
            border: "1px solid #e5b1b1",
            background: "#fff1f1",
            borderRadius: "6px",
            color: "#7a1f1f",
          }}
        >
          <strong>{error.title}</strong>
          <p style={{ margin: "6px 0 0" }}>{error.message}</p>
        </div>
      )}

      {data && (
        <div style={{ marginTop: "20px", display: "grid", gap: "18px" }}>
          <section>
            <h2 style={{ marginBottom: "8px" }}>Tag Accuracy</h2>
            <TagStats tagAccuracy={data.tag_accuracy} />
          </section>

          <section>
            <h2 style={{ marginBottom: "8px" }}>Rating Accuracy</h2>
            <RatingStats ratingAccuracy={data.rating_accuracy} />
          </section>

          <section>
            <h2 style={{ marginBottom: "8px" }}>Average Solve Time</h2>
            <p>{data.average_solve_time} ms</p>
          </section>

          <section>
            <h2 style={{ marginBottom: "8px" }}>Insights</h2>
            <Insights insights={data.insights} />
          </section>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
