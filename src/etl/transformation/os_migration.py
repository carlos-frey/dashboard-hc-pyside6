import pandas as pd
import numpy as np

def migrar_dados_servico(caminho_os_antiga=None, caminho_os_atual=None):
    """
    Migra e unifica os dados das ordens de serviço antigas e recentes
    para um novo formato em um único DataFrame.
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

    # 3. Mapeamento
    # Mapeamos colunas de ambos os formatos para um formato padrão interno
    mapeamento_recente = {
        'O.S': 'OS',
        'Tipo': 'Equipamento',
        'Data Início SE': 'Abertura',
        'Data Conclusão SE': 'Fechamento',
        'Fornecedor': 'Serviço;Assistência',
        'Identificador (Patrimônio, ID, TAG)': 'Identificador'
    }
    
    mapeamento_antigo = {
        'Serviço': 'Serviço;Assistência' # Simplificação, pois o antigo tem duas colunas
    }

    # Processar Recente
    if not df_recente.empty:
        df_recente.rename(columns=mapeamento_recente, inplace=True)
        if 'Identificador' not in df_recente.columns:
            df_recente['Identificador'] = ''
    
    # Processar Antigo
    if not df_contrato_sl.empty:
        df_contrato_sl.rename(columns=mapeamento_antigo, inplace=True)
        # Mapear coluna de data para 'Abertura' — o formato antigo não tem esse nome por padrão
        if 'Abertura' not in df_contrato_sl.columns:
            for _date_col in ('Data', 'Data Abertura', 'Data de Abertura', 'Data Início', 'Data inicio', 'Data_Abertura'):
                if _date_col in df_contrato_sl.columns:
                    df_contrato_sl.rename(columns={_date_col: 'Abertura'}, inplace=True)
                    break
            else:
                print("Aviso: coluna de data não encontrada no arquivo OS antigo. Histórico de datas não disponível.")
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

    # 4. Unificar
    # Usamos as colunas do df_recente como base se existir, senão as do antigo
    if not df_recente.empty:
        df_migrado = df_recente.copy()
        if not df_contrato_sl.empty:
            # Garantir que df_contrato_sl tenha as mesmas colunas (pelo menos as essenciais)
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
        df_custo = df['Custo'].copy()
        df_custo = df_custo.astype(str).str.replace(r'[^\d,\.]', '', regex=True)
        df_custo = df_custo.str.replace(',', '.')
        custo_num = pd.to_numeric(df_custo, errors='coerce').fillna(0)
        return float(custo_num.sum())
    return 0.0

def extrair_historico_os(df, excluir_custo_zero=False):
    if 'Abertura' in df.columns:
        df_temp = df.copy()
        
        # Limpeza robusta de custo para filtro
        if excluir_custo_zero and 'Custo' in df_temp.columns:
            custo_str = df_temp['Custo'].astype(str).str.replace(r'[^\d,\.]', '', regex=True).str.replace(',', '.')
            custo_num = pd.to_numeric(custo_str, errors='coerce').fillna(0)
            df_temp = df_temp[custo_num > 0]
            
        # Conversão de data flexível
        # Tentamos primeiro o formato DD/MM/YYYY que é comum no legado
        # dayfirst=True ajuda muito aqui.
        df_temp['Data'] = pd.to_datetime(df_temp['Abertura'], errors='coerce', dayfirst=True)
        
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
