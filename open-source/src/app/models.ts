export interface User {
  id: number;
  username: string;
  display_name?: string;
}

export interface Post {
  id: number;
  user_id: number;
  author?: User;
  title: string;
  subtitle?: string;
  created_at: string;
  views_count?: number;
  content?: string;
  thumbnail?: string;
}
