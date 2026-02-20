export interface User {
  id: number;
  username: string;
  display_name?: string;
}

export interface Post {
  id: number;
  user_id: number;
  author?: User;
  content: string;
  created_at: string;
  likes_count?: number;
  liked_by_me?: boolean;
}
