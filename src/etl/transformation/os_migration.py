import pandas as pd
import numpy as np

# Nome canônico da coluna de serviço/assistência.
# IMPORTANTE: não usar ';' no nome — é o separador do CSV e quebraria o
# cabeçalho ao exportar (df.to_csv(sep=';')).
COL_SERVICO = 'Serviço / Assistência'


def _parse_custo_novo(serie):
    """Formato NOVO: ponto = separador decimal (ex.: '3519.58', '13750')."""
    s = serie.astype(str).str.replace(r'[^\d.]', '', regex=True)
    return pd.to_numeric(s, errors='coerce')


def _parse_custo_antigo(serie):
    """Formato ANTIGO (BR): ponto = milhar, vírgula = decimal (ex.: '8.990,00')."""
    s = serie.astype(str).str.replace(r'[^\d,]', '', regex=True)  # remove ponto de milhar
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce')


def _desc_antigo(row):
    """Descrição do formato antigo: tipo de serviço + assistência (empresa)."""
    serv = str(row['Serviço']).strip() if 'Serviço' in row and pd.notna(row['Serviço']) else ''
    assist = str(row['Assistência']).strip() if 'Assistência' in row and pd.notna(row['Assistência']) else ''
    partes = [p for p in (serv, assist) if p and p.lower() != 'nan']
    return ' — '.join(partes)


def migrar_dados_servico(caminho_os_antiga=None, caminho_os_atual=None):
    """
    Migra e unifica os dados das ordens de serviço antigas e recentes
    para um formato canônico único.

    A "conversão" não é apenas de nomes de coluna: cada formato tem
    convenções de VALOR diferentes (datas BR vs ISO; números BR vs US),
    então normalizamos os valores por origem ANTES de concatenar.
    """
    if not caminho_os_antiga and not caminho_os_atual:
        raise ValueError("Pelo menos um arquivo de Ordens de Serviço (antigo ou atual) deve ser fornecido.")

    df_recente = pd.DataFrame()
    df_contrato_sl = pd.DataFrame()

    # 1. Carregar planilha atual (se fornecida)
    if caminho_os_atual:
        try:
            df_recente = pd.read_csv(caminho_os_atual, sep=';', engine='python')
            print(f"DEBUG: Planilha atual carregada: {len(df_recente)} linhas.")
        except Exception as e:
            print(f"Aviso: Erro ao carregar planilha de OS atual: {e}")

    # 2. Carregar planilha antiga (se fornecida)
    if caminho_os_antiga:
        try:
            df_contrato_sl = pd.read_csv(caminho_os_antiga, sep=';', skiprows=[0], engine='python')
            print(f"DEBUG: Planilha antiga carregada: {len(df_contrato_sl)} linhas.")
        except Exception as e:
            print(f"Aviso: Erro ao carregar planilha de OS antiga: {e}")

    if df_recente.empty and df_contrato_sl.empty:
        raise ValueError("Nenhum dado pôde ser extraído das planilhas fornecidas.")

    # 3. Mapeamento de colunas para o formato canônico interno
    mapeamento_recente = {
        'O.S': 'OS',
        'Tipo': 'Equipamento',
        'Data Início SE': 'Abertura',
        'Data Conclusão SE': 'Fechamento',
        'Fornecedor': COL_SERVICO,
        'Identificador (Patrimônio, ID, TAG)': 'Identificador'
    }

    # ── Processar formato RECENTE (novo) ──────────────────────────────
    if not df_recente.empty:
        df_recente.rename(columns=mapeamento_recente, inplace=True)
        if 'Identificador' not in df_recente.columns:
            df_recente['Identificador'] = ''
        # Datas ISO ("2024-06-11 10:42:53") — SEM dayfirst (ISO é inequívoco;
        # dayfirst=True trocaria mês/dia, ex.: 11/jun -> 06/nov).
        if 'Abertura' in df_recente.columns:
            df_recente['Abertura'] = pd.to_datetime(df_recente['Abertura'], errors='coerce')
        # Custo em convenção US (ponto decimal)
        if 'Custo' in df_recente.columns:
            df_recente['Custo'] = _parse_custo_novo(df_recente['Custo'])

    # ── Processar formato ANTIGO (BR) ─────────────────────────────────
    if not df_contrato_sl.empty:
        # Descrição: combina o tipo de serviço e a assistência (empresa),
        # alinhando-se ao 'Fornecedor' do formato novo.
        df_contrato_sl[COL_SERVICO] = df_contrato_sl.apply(_desc_antigo, axis=1)

        # Mapear coluna de data para 'Abertura' — o formato antigo nem sempre usa esse nome
        if 'Abertura' not in df_contrato_sl.columns:
            for _date_col in ('Data', 'Data Abertura', 'Data de Abertura', 'Data Início', 'Data inicio', 'Data_Abertura'):
                if _date_col in df_contrato_sl.columns:
                    df_contrato_sl.rename(columns={_date_col: 'Abertura'}, inplace=True)
                    break
            else:
                print("Aviso: coluna de data não encontrada no arquivo OS antigo. Histórico de datas não disponível.")

        # Datas BR ("20/02/2018 08:00") — dayfirst=True
        if 'Abertura' in df_contrato_sl.columns:
            df_contrato_sl['Abertura'] = pd.to_datetime(df_contrato_sl['Abertura'], errors='coerce', dayfirst=True)

        # Custo em convenção BR (ponto = milhar, vírgula = decimal)
        if 'Custo' in df_contrato_sl.columns:
            df_contrato_sl['Custo'] = _parse_custo_antigo(df_contrato_sl['Custo'])

        # Gerar Identificador — strip para evitar espaços que causam '' ou falsos matches
        def gerar_identificador(row):
            tag = str(row['TAG']).strip() if 'TAG' in row and pd.notna(row['TAG']) else ''
            pat = str(row['Patrimônio']).strip() if 'Patrimônio' in row and pd.notna(row['Patrimônio']) else ''
            if tag and pat:
                return f"{tag},{pat}"
            return tag or pat

        df_contrato_sl['Identificador'] = df_contrato_sl.apply(gerar_identificador, axis=1)
        # Descartar linhas sem identificador — não podem ser vinculadas a nenhum equipamento
        df_contrato_sl = df_contrato_sl[df_contrato_sl['Identificador'] != '']

    # 4. Unificar — colunas do df_recente como base se existir, senão as do antigo
    if not df_recente.empty:
        df_migrado = df_recente.copy()
        if not df_contrato_sl.empty:
            for col in df_migrado.columns:
                if col not in df_contrato_sl.columns:
                    df_contrato_sl[col] = np.nan
            df_migrado = pd.concat([df_migrado, df_contrato_sl[df_migrado.columns]], ignore_index=True)
    else:
        df_migrado = df_contrato_sl.copy()

    print(f"DEBUG: Processamento de Ordens de Serviço finalizado. Total: {len(df_migrado)} linhas.")
    return df_migrado


def obter_total_os_emitidas(df):
    return len(df)


def obter_total_gasto_os(df):
    if 'Custo' in df.columns:
        custo_num = pd.to_numeric(df['Custo'], errors='coerce').fillna(0)
        return float(custo_num.sum())
    return 0.0


def extrair_historico_os(df, excluir_custo_zero=False):
    if 'Abertura' in df.columns:
        df_temp = df.copy()

        if excluir_custo_zero and 'Custo' in df_temp.columns:
            custo_num = pd.to_numeric(df_temp['Custo'], errors='coerce').fillna(0)
            df_temp = df_temp[custo_num > 0]

        # 'Abertura' já vem como datetime canônico de migrar_dados_servico;
        # pd.to_datetime é um no-op seguro caso receba strings.
        df_temp['Data'] = pd.to_datetime(df_temp['Abertura'], errors='coerce')

        dropped = df_temp['Data'].isna().sum()
        if dropped > 0:
            print(f"DEBUG: {dropped} linhas de OS descartadas por erro na data.")

        df_temp = df_temp.dropna(subset=['Data'])
        df_temp['Ano'] = df_temp['Data'].dt.year.astype(int)
        df_temp['Mes'] = df_temp['Data'].dt.month.astype(int)

        historico = df_temp.groupby(['Ano', 'Mes']).size().reset_index(name='Contagem')

        resultado = {}
        for _, row in historico.iterrows():
            y = int(row['Ano'])
            m = int(row['Mes'])
            c = int(row['Contagem'])
            if y not in resultado:
                resultado[y] = {m_idx: 0 for m_idx in range(1, 13)}
            resultado[y][m] = c

        return resultado
    return {}
