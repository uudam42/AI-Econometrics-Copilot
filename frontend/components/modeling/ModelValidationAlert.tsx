interface ModelValidationAlertProps {
  errors: string[];
}

export function ModelValidationAlert({ errors }: ModelValidationAlertProps) {
  if (errors.length === 0) return null;
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3">
      <p className="mb-1 text-sm font-semibold text-red-800">
        Cannot run analysis — please fix the following:
      </p>
      <ul className="list-inside list-disc space-y-0.5 text-sm text-red-700">
        {errors.map((e, i) => (
          <li key={i}>{e}</li>
        ))}
      </ul>
    </div>
  );
}
