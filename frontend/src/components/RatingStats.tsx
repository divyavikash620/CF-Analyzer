interface RatingStatsProps {
  ratingAccuracy?: Record<string, number>;
}

function parseLowerBound(bucket: string): number {
  const match = bucket.match(/^(\d+)(?:-\d+|\+)?$/);
  if (!match) {
    return Number.POSITIVE_INFINITY;
  }
  return Number(match[1]);
}

function RatingStats({ ratingAccuracy }: RatingStatsProps) {
  const sortedBuckets = Object.entries(ratingAccuracy ?? {}).sort(([a], [b]) => parseLowerBound(a) - parseLowerBound(b));

  if (sortedBuckets.length === 0) {
    return <p>No rating stats available.</p>;
  }

  return (
    <ul>
      {sortedBuckets.map(([bucket, value]) => (
        <li key={bucket}>
          {bucket}: {value}%
        </li>
      ))}
    </ul>
  );
}

export default RatingStats;
