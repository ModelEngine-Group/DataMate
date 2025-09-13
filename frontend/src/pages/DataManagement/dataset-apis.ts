const datasetApiBase = "/api";

export async function getDatasetStatisticsUsingGet() {
  const res = await fetch(`${datasetApiBase}/datasets/statistics`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to fetch dataset statistics");
  const response = await res.json();
  return response.data;
}

export async function queryDatasetsUsingGet(params: { [key: string]: any }) {
 console.log(params);
 
  const res = await fetch(`${datasetApiBase}/datasets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error("Failed to fetch datasets");
  }
  const response = await res.json();
  return response.data;
}
