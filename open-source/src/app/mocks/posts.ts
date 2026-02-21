import { Post } from '../models';
export const MOCK_POSTS: Post[] = [
  {
    id: 1001,
    user_id: 1,
    title: 'Edmonton region touted as unique location for federal defence initiative.',
    subtitle: "Brent Jensen with Edmonton Global joins Alberta Primetime host Michael Higgins to discuss an alliance between his organization and other Edmonton entities aiming to establish the Edmonton region as a defence-related hub.",
    created_at: '2026-02-20T16:05:00Z',
    views_count: 12,
    author: { id: 1, username: 'CTV', display_name: 'CTV News' }
  },
  {
    id: 1002,
    user_id: 2,
    title: 'No residential parking ban expected for Edmonton snow removal.',
    subtitle: "Deployment of 100 additional contractors combined with lower than anticipated snowfall have helped city clear main roads to regular standard",
    created_at: '2026-02-20T15:10:00Z',
    views_count: 27,
    author: { id: 2, username: 'alice', display_name: 'Edmonton Journal' }
  },
  {
    id: 1003,
    user_id: 3,
    title: 'Deployment of 100 additional contractors combined with lower than anticipated snowfall have helped city clear main roads to regular standard.',
    subtitle:"Televised address comes 1 week before provincial budget",
    created_at: '2026-02-20T14:35:00Z',
    views_count: 41,
    author: { id: 3, username: 'bob', display_name: 'CBC' }
  }
];