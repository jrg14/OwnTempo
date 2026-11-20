type ModuleCardProps = {
  icon: string;
  title: string;
  description: string;
};

export function ModuleCard({ icon, title, description }: ModuleCardProps) {
  return (
    <article className="module-card">
      <span aria-hidden="true" className="module-card__icon">
        {icon}
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

