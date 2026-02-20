interface TagStatsProps {
  tagAccuracy?: Record<string, number>;
}

function TagStats({ tagAccuracy }: TagStatsProps) {
  const entries = Object.entries(tagAccuracy ?? {}).sort(([, a], [, b]) => b - a);

  if (entries.length === 0) {
    return <p>No tag stats available.</p>;
  }

  return (
    <ul>
      {entries.map(([tag, value]) => (
        <li key={tag}>
          {tag}: {value}%
        </li>
      ))}
    </ul>
  );
}

export default TagStats;
