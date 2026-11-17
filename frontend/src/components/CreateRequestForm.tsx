
import type { FormEvent } from "react"
import type { RequestForm } from "../types/request"

type CreateRequestFormProps = {
  form: RequestForm
  onFormChange: (form: RequestForm) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export default function CreateRequestForm({
  form,
  onFormChange,
  onSubmit,
}: CreateRequestFormProps) {
  return (
    <section className="panel">
      <h2>Create a service request</h2>

      <p className="panel-description">
        Describe the issue that needs attention.
      </p>

      <form className="request-form" onSubmit={onSubmit}>
        <label>
          Request title

          <input
            required
            minLength={3}
            maxLength={150}
            value={form.title}
            onChange={(event) =>
              onFormChange({
                ...form,
                title: event.target.value,
              })
            }
            placeholder="e.g. Broken classroom fan"
          />
        </label>

        <label>
          Description

          <textarea
            required
            minLength={5}
            value={form.description}
            onChange={(event) =>
              onFormChange({
                ...form,
                description: event.target.value,
              })
            }
            placeholder="Explain the problem..."
            rows={4}
          />
        </label>

        <label>
          Category

          <select
            value={form.category}
            onChange={(event) =>
              onFormChange({
                ...form,
                category: event.target.value,
              })
            }
          >
            <option value="Electrical">Electrical</option>
            <option value="Plumbing">Plumbing</option>
            <option value="Cleaning">Cleaning</option>
            <option value="Equipment">Equipment</option>
            <option value="Other">Other</option>
          </select>
        </label>

        <button className="primary-button" type="submit">
          Submit request
        </button>
      </form>
    </section>
  )
}
