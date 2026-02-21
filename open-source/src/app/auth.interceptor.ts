import { HttpInterceptorFn } from '@angular/common/http';
const mutatingMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const csrfToken = getCookie('csrftoken');
  const shouldAttachCsrf = mutatingMethods.has(req.method.toUpperCase()) && !!csrfToken;

  const cloned = req.clone({
    withCredentials: true,
    setHeaders: shouldAttachCsrf ? { 'X-CSRFToken': csrfToken! } : {}
  });

  return next(cloned);
};
