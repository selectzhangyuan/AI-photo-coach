import { http } from "./http";

export interface UploadImageResponse {
  image_id: string;
  mime_type: string;
  size_bytes: number;
  width: number | null;
  height: number | null;
  object_key: string;
}

export async function uploadImage(file: File): Promise<UploadImageResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await http.post<UploadImageResponse>("/images/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

