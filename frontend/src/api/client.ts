import axios from "axios";
import type {
  AnalyticsResponse,
  AuditLogEntry,
  BatchReport,
  Customer,
  DashboardKpis,
  Payment,
  RecoveryAttempt,
  RecoveryBatch,
} from "../types";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
});

export const endpoints = {
  kpis: () => api.get<DashboardKpis>("/dashboard/kpis").then((r) => r.data),
  analytics: () => api.get<AnalyticsResponse>("/dashboard/analytics").then((r) => r.data),
  failedPayments: () => api.get<Payment[]>("/dashboard/failed-payments").then((r) => r.data),

  listPayments: (params?: { status?: string; batch_id?: string }) =>
    api.get<Payment[]>("/payments", { params }).then((r) => r.data),
  getPayment: (id: string) => api.get<Payment>(`/payments/${id}`).then((r) => r.data),
  getPaymentAttempts: (id: string) => api.get<RecoveryAttempt[]>(`/payments/${id}/attempts`).then((r) => r.data),

  getCustomer: (id: string) => api.get<Customer>(`/customers/${id}`).then((r) => r.data),

  evaluatePayment: (paymentId: string) =>
    api.post<RecoveryAttempt>(`/recovery/evaluate/${paymentId}`).then((r) => r.data),
  executeAttempt: (attemptId: string) =>
    api.post<RecoveryAttempt>(`/recovery/attempts/${attemptId}/execute`).then((r) => r.data),

  listBatches: () => api.get<RecoveryBatch[]>("/batches").then((r) => r.data),
  getBatch: (id: string) => api.get<RecoveryBatch>(`/batches/${id}`).then((r) => r.data),
  getBatchReport: (id: string) => api.get<BatchReport>(`/batches/${id}/report`).then((r) => r.data),
  createBatch: (name: string, paymentIds?: string[]) =>
    api.post<RecoveryBatch>("/batches", { name, payment_ids: paymentIds }).then((r) => r.data),

  paymentAudit: (id: string) => api.get<AuditLogEntry[]>(`/audit/payment/${id}`).then((r) => r.data),
  batchAudit: (id: string) => api.get<AuditLogEntry[]>(`/audit/batch/${id}`).then((r) => r.data),
};
