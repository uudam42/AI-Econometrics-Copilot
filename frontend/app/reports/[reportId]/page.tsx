import PageClient from "./_client";

export const revalidate = 0;

export async function generateStaticParams() {
  return [];
}

export default function Page() {
  return <PageClient />;
}
