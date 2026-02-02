export const HTTP_STATUS = {
	OK: { code: 200, label: 'OK' },
	Created: { code: 201, label: 'Created' },
	NoContent: { code: 204, label: 'No Content' },
	BadRequest: { code: 400, label: 'Bad Request' },
	Unauthorized: { code: 401, label: 'Unauthorized' },
	NotFound: { code: 404, label: 'Not Found' },
	InternalServerError: { code: 500, label: 'Internal Server Error' },
	GatewayTimeout: { code: 504, label: 'Gateway Timeout' }
} as const

export type HTTP_STATUS_TYPE = (typeof HTTP_STATUS)[keyof typeof HTTP_STATUS]
