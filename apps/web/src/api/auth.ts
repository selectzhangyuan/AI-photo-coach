import { http } from "./http";

export interface UserProfile {
  id: string;
  email: string;
  nickname: string | null;
  avatar_url: string | null;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterParams {
  email: string;
  password: string;
  nickname?: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export function register(params: RegisterParams) {
  return http.post<TokenResponse>("/auth/register", params);
}

export function login(params: LoginParams) {
  return http.post<TokenResponse>("/auth/login", params);
}

export function refreshTokenRequest(token: string) {
  return http.post<TokenResponse>("/auth/refresh", { refresh_token: token });
}

export function logout() {
  return http.post("/auth/logout");
}

export function getProfile() {
  return http.get<UserProfile>("/users/me");
}

export function updateProfile(data: { nickname?: string; avatar_url?: string }) {
  return http.patch<UserProfile>("/users/me", data);
}

export function changePassword(data: { current_password: string; new_password: string }) {
  return http.post("/users/me/change-password", data);
}
