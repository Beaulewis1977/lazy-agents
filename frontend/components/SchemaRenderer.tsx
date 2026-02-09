"use client";

interface SchemaRendererProps {
  schema: Record<string, unknown> | null | undefined;
  depth?: number;
}

export default function SchemaRenderer({ schema, depth = 0 }: SchemaRendererProps) {
  if (!schema) {
    return (
      <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
        No schema available
      </div>
    );
  }

  const isObjectSchema = schema.type === 'object' && schema.properties;

  if (isObjectSchema) {
    const properties = schema.properties as Record<string, Record<string, unknown>>;
    const required = (schema.required as string[]) || [];

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {Object.entries(properties).map(([propName, propSchema]) => (
          <PropertyRow
            key={propName}
            name={propName}
            schema={propSchema}
            required={required.includes(propName)}
            depth={depth}
          />
        ))}
      </div>
    );
  }

  return (
    <pre
      style={{
        background: 'var(--color-bg-tertiary)',
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--font-size-sm)',
        padding: 'var(--space-4)',
        borderRadius: 'var(--radius-md)',
        overflowX: 'auto',
        color: 'var(--color-text-secondary)',
        margin: 0,
      }}
    >
      {JSON.stringify(schema, null, 2)}
    </pre>
  );
}

interface PropertyRowProps {
  name: string;
  schema: Record<string, unknown>;
  required: boolean;
  depth: number;
}

function PropertyRow({ name, schema, required, depth }: PropertyRowProps) {
  const type = schema.type as string | undefined;
  const description = schema.description as string | undefined;
  const enumArray = schema.enum as Array<string | number | boolean> | undefined;
  const defaultValue = schema.default as string | number | boolean | null | undefined;

  const isNestedObject = Boolean(type === 'object' && schema.properties);
  const isArray = Boolean(type === 'array' && schema.items);

  return (
    <div
      style={{
        background: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-3)',
        paddingLeft: depth > 0 ? `calc(var(--space-3) + ${depth * 16}px)` : 'var(--space-3)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)', flexWrap: 'wrap' }}>
        <code
          style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-accent)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-medium)',
          }}
        >
          {name}
        </code>

        {type && (
          <span className="badge badge-neutral" style={{ fontSize: 'var(--font-size-xs)' }}>
            {type}
          </span>
        )}

        {required && (
          <span className="badge badge-error" style={{ fontSize: 'var(--font-size-xs)' }}>
            required
          </span>
        )}
      </div>

      {description && (
        <div
          style={{
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--font-size-sm)',
            marginBottom: enumArray || defaultValue !== undefined ? 'var(--space-2)' : 0,
          }}
        >
          {description}
        </div>
      )}

      {enumArray && enumArray.length > 0 && (
        <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', marginBottom: defaultValue !== undefined ? 'var(--space-1)' : 0 }}>
          Allowed: {enumArray.map(v => JSON.stringify(v)).join(', ')}
        </div>
      )}

      {defaultValue !== undefined && (
        <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
          Default: {JSON.stringify(defaultValue)}
        </div>
      )}

      {isNestedObject && (
        <div style={{ marginTop: 'var(--space-3)' }}>
          <SchemaRenderer schema={schema} depth={depth + 1} />
        </div>
      )}

      {isArray && (
        <div style={{ marginTop: 'var(--space-3)' }}>
          <div
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-2)',
              fontWeight: 'var(--font-weight-medium)',
            }}
          >
            Items:
          </div>
          <SchemaRenderer schema={schema.items as Record<string, unknown>} depth={depth + 1} />
        </div>
      )}
    </div>
  );
}
