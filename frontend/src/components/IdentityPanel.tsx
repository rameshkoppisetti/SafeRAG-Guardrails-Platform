type IdentityPanelProps = {
  tenantId: string;
  userId: string;
  roles: string;
  onTenantIdChange: (value: string) => void;
  onUserIdChange: (value: string) => void;
  onRolesChange: (value: string) => void;
};

export function IdentityPanel({
  tenantId,
  userId,
  roles,
  onTenantIdChange,
  onUserIdChange,
  onRolesChange,
}: IdentityPanelProps) {
  return (
    <section className="panel">
      <h2>Identity & ACL</h2>
      <label>
        Tenant ID
        <input value={tenantId} onChange={(e) => onTenantIdChange(e.target.value)} />
      </label>
      <label>
        User ID
        <input value={userId} onChange={(e) => onUserIdChange(e.target.value)} />
      </label>
      <label>
        Roles / ACL
        <input value={roles} onChange={(e) => onRolesChange(e.target.value)} placeholder="support,employee" />
      </label>
    </section>
  );
}
