const datasetApiBase = "/api/datasets";

export async function fetchDatasetStatistics() {
  const res = await fetch(`${datasetApiBase}/statistics`);
  if (!res.ok) throw new Error("Failed to fetch dataset statistics");
  const data = await res.json();
  return data;
}
