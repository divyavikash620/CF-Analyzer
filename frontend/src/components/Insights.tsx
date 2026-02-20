interface InsightsProps {
  insights?: string[];
}

function Insights({ insights }: InsightsProps) {
  const items = insights ?? [];

  if (items.length === 0) {
    return <p>No major weaknesses detected.</p>;
  }

  return (
    <ul>
      {items.map((insight, index) => (
        <li key={`${index}-${insight}`}>{insight}</li>
      ))}
    </ul>
  );
}

export default Insights;
