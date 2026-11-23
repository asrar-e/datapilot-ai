const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "";


export interface Dataset {
  dataset_id: string;
  dataset_name: string;
  original_filename: string;
  table_name: string;
  file_type: string;
  row_count: number;
  column_count: number;
  ingestion_status: string;
  uploaded_at: string;
}

export interface DatasetListResponse {
  count: number;
  datasets: Dataset[];
}

export interface QueryResponse {
  dataset_id: string;
  question: string;
  status: string;
  generated_query: {
    sql: string;
    explanation?: string;
    chart_type?: string;
    chart_x?: string;
    chart_y?: string;
  };
  result: {
    columns: string[];
    rows: Record<string, unknown>[] | unknown[][];
    row_count: number;
    executed_sql?: string;
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const message =
      error?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getDatasets() {
  return request<DatasetListResponse>("/datasets");
}

export function uploadDataset(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return request<{ message: string; dataset: Dataset }>(
    "/datasets/upload",
    {
      method: "POST",
      body: formData,
    },
  );
}

export function askDataset(
  datasetId: string,
  question: string,
) {
  return request<QueryResponse>(
    `/datasets/${datasetId}/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    },
  );
}
