type IconName =
  | 'activity'
  | 'arrow-left'
  | 'arrow-right'
  | 'calendar'
  | 'cart'
  | 'check'
  | 'chevron'
  | 'close'
  | 'clock'
  | 'checkmark'
  | 'edit'
  | 'heart'
  | 'home'
  | 'logout'
  | 'plus'
  | 'settings'
  | 'trash'
  | 'users'
  | 'wallet';

type IconProps = {
  name: IconName;
  size?: number;
};

const paths: Record<IconName, React.ReactNode> = {
  activity: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  'arrow-left': <><path d="m15 18-6-6 6-6" /><path d="M9 12h10" /></>,
  'arrow-right': <><path d="m9 18 6-6-6-6" /><path d="M5 12h10" /></>,
  calendar: <><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16" /></>,
  cart: <><path d="M6 8h12l-1 11H7L6 8Z" /><path d="M9 8a3 3 0 0 1 6 0" /></>,
  check: <><path d="M9 11.5 11 13l4-5" /><path d="M5 4h14v16H5z" /></>,
  chevron: <path d="m8 10 4 4 4-4" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  checkmark: <path d="m5 12 4 4L19 6" />,
  edit: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" /></>,
  heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.7-7.5 1.1-1.1a5.5 5.5 0 0 0 0-7.8Z" />,
  home: <><path d="m4 11 8-7 8 7" /><path d="M6 10v10h12V10" /></>,
  logout: <><path d="M10 5H5v14h5" /><path d="m14 8 4 4-4 4M8 12h10" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6 1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" /></>,
  trash: <><path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></>,
  wallet: <><path d="M4 6h15v13H4z" /><path d="M4 9V5h13M15 12h6v4h-6z" /></>,
};

export function Icon({ name, size = 20 }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
      width={size}
    >
      {paths[name]}
    </svg>
  );
}
