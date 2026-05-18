export const questionEndpoints = {
  create: '/api/v1/questions',
  submit: (questionId: number) => `/api/v1/questions/${questionId}/submit`,
  review: (questionId: number) => `/api/v1/questions/${questionId}/review`,
  reviewQueue: '/api/v1/questions/review-queue',
  archiveForEdit: (questionId: number) => `/api/v1/questions/${questionId}/archive-for-edit`,
  bulkImport: '/api/v1/questions/import',
};
