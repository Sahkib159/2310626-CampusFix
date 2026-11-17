export type RequestStatus =
  | "pending"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "cancelled"

export type ServiceRequest = {
  id: number
  title: string
  description: string
  category: string
  status: RequestStatus
}

export type RequestForm = {
  title: string
  description: string
  category: string
}

export type EditForm = RequestForm & {
  status: RequestStatus
}