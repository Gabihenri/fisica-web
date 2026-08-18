-- Física Web: observações escritas ou transcritas por voz, vinculadas
-- ao participante e à sessão de experimento.

create table if not exists public.observacoes_participantes (
  id uuid primary key default gen_random_uuid(),
  participante_id uuid not null references public.participantes(id) on delete cascade,
  experimento_id uuid not null references public.experimentos(id) on delete cascade,
  grupo_id uuid not null references public.grupos_experimentais(id) on delete cascade,
  observacao text not null default '',
  origem text not null default 'escrita' check (origem in ('escrita','voz_transcrita')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (participante_id, experimento_id)
);

create index if not exists idx_observacoes_participantes_grupo on public.observacoes_participantes(grupo_id);
create index if not exists idx_observacoes_participantes_experimento on public.observacoes_participantes(experimento_id);

alter table public.observacoes_participantes enable row level security;

create policy "observacoes_select_grupo" on public.observacoes_participantes
for select using (exists (select 1 from public.usuarios_grupos ug where ug.user_id = auth.uid() and ug.grupo_id = observacoes_participantes.grupo_id and ug.ativo = true));

create policy "observacoes_insert_grupo" on public.observacoes_participantes
for insert with check (exists (select 1 from public.usuarios_grupos ug where ug.user_id = auth.uid() and ug.grupo_id = observacoes_participantes.grupo_id and ug.ativo = true));

create policy "observacoes_update_grupo" on public.observacoes_participantes
for update using (exists (select 1 from public.usuarios_grupos ug where ug.user_id = auth.uid() and ug.grupo_id = observacoes_participantes.grupo_id and ug.ativo = true))
with check (exists (select 1 from public.usuarios_grupos ug where ug.user_id = auth.uid() and ug.grupo_id = observacoes_participantes.grupo_id and ug.ativo = true));

create policy "observacoes_delete_grupo" on public.observacoes_participantes
for delete using (exists (select 1 from public.usuarios_grupos ug where ug.user_id = auth.uid() and ug.grupo_id = observacoes_participantes.grupo_id and ug.ativo = true));

create or replace function public.set_observacoes_participantes_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_observacoes_participantes_updated_at on public.observacoes_participantes;
create trigger trg_observacoes_participantes_updated_at
before update on public.observacoes_participantes
for each row execute function public.set_observacoes_participantes_updated_at();
