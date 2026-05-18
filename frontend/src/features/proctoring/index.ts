export const proctorEndpoints = {
  events: (attemptId: number) => `/api/v1/attempts/${attemptId}/proctoring/events`,
  snapshots: (attemptId: number) => `/api/v1/attempts/${attemptId}/proctoring/snapshots`,
  intervene: (attemptId: number) => `/api/v1/attempts/${attemptId}/proctoring/intervene`,
};
