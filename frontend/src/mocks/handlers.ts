import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/users/me', () => {
    return HttpResponse.json({
      email: 'test@example.com',
      fullName: 'Test User',
      roles: ['Admin'],
    });
  }),
];
