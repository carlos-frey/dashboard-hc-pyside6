import pandas as pd

def migrar_dados_servico(caminho_os_antiga=None, caminho_os_atual=None):
    """
    Migra e unifica os dados das ordens de serviço antigas e recentes
    para um novo formato em um único DataFrame.
    
    Aceita pelo menos uma das planilhas. Ignora e sinaliza caso uma esteja faltando.
    """
    if not caminho_os_antiga and not caminho_os_atual:
        raise ValueError("Pelo menos um arquivo de Ordens de Serviço (antigo ou atual) deve ser fornecido.")

    df_recente = pd.DataFrame()
    df_contrato_sl = pd.DataFrame()
    
    # 1. Carregar planilha atual (se fornecida)
    if caminho_os_atual:
        try:
            df_recente = pd.read_csv(caminho_os_atual, sep=';', engine='python')
            print(f"Planilha atual carregada: {caminho_os_atual}")
        except FileNotFoundError:
            print(f"Aviso: Planilha de OS atual não encontrada em '{caminho_os_atual}'.")

    # 2. Carregar planilha antiga (se fornecida)
    if caminho_os_antiga:
        try:
            # O formato antigo usa skiprows=[0]
            df_contrato_sl = pd.read_csv(caminho_os_antiga, sep=';', skiprows=[0], engine='python')
            print(f"Planilha antiga carregada: {caminho_os_antiga}")
        except FileNotFoundError:
            print(f"Aviso: Planilha de OS antiga não encontrada em '{caminho_os_antiga}'.")

    # Se ambas falharem na leitura por arquivo inexistente apesar de o path ser fornecido
    if df_recente.empty and df_contrato_sl.empty:
        raise ValueError("Nenhum dado pôde ser extraído das planilhas fornecidas.")

    # 3. Estabelecer o esquema base
    colunas_esperadas = [
        'OS', 'Equipamento', 'Modelo', 'Fabricante', 'Abertura', 'Fechamento', 
        'Serviço;Assistência', 'Custo', 'Identificador (Patrimônio, ID, TAG)'
    ]
    
    if not df_recente.empty:
        df_migrado = df_recente.copy()
        if 'Identificador (Patrimônio, ID, TAG)' not in df_migrado.columns:
            df_migrado['Identificador (Patrimônio, ID, TAG)'] = ''
    else:
        # Cria um DataFrame vazio com a estrutura das colunas modernas caso só tenha a velha
        df_migrado = pd.DataFrame(columns=colunas_esperadas)

    # 4. Mapeamento do formato legado para o novo formato
    mapeamento = {
        'O.S': 'OS', 'Tipo': 'Equipamento', 'Modelo': 'Modelo', 'Marca': 'Fabricante',
        'Data Início SE': 'Abertura', 'Data Conclusão SE': 'Fechamento',
        'Fornecedor': 'Serviço;Assistência', 'Custo': 'Custo'
    }

    # 5. Iterar e injetar linhas antigas, se existirem
    novas_linhas = []
    if not df_contrato_sl.empty:
        for _, row in df_contrato_sl.iterrows():
            nova_linha = {col: None for col in df_migrado.columns}
            
            # Aplica o de-para iterativo
            for col_recente, col_sl in mapeamento.items():
                if col_sl in row:
                    nova_linha[col_recente] = row[col_sl]
            
            # Gera o Identificador único a partir da TAG + Patrimônio
            tag = str(row['TAG']) if 'TAG' in row and pd.notna(row['TAG']) else ''
            patrimonio = str(row['Patrimônio']) if 'Patrimônio' in row and pd.notna(row['Patrimônio']) else ''
            identificador = f"{tag},{patrimonio}" if tag and patrimonio else tag or patrimonio
            
            nova_linha['Identificador (Patrimônio, ID, TAG)'] = identificador
            novas_linhas.append(nova_linha)

    # 6. Concatena os DataFrames
    if novas_linhas:
        df_migrado = pd.concat([df_migrado, pd.DataFrame(novas_linhas)], ignore_index=True)
    
    print("Processamento de Ordens de Serviço finalizado.")
    return df_migrado

def obter_total_os_emitidas(df):
    """Retorna o total de ordens de serviço emitidas."""
    return len(df)

def obter_total_gasto_os(df):
    """Calcula e retorna o total gasto em ordens de serviço."""
    if 'Custo' in df.columns:
        df_custo = df['Custo'].copy()
        # Converte para string e limpa os caracteres monetários
        df_custo = df_custo.astype(str).str.replace(r'[^\d,\.]', '', regex=True)
        # Substitui vírgula por ponto se necessário, em casos gerais do brasil
        df_custo = df_custo.str.replace(',', '.')
        # Como as vezes pode ficar com mais de um ponto (ex 1.000.00), é melhor uma limpeza robusta
        # mas como simplificação, coerce é usado:
        custo_num = pd.to_numeric(df_custo, errors='coerce').fillna(0)
        return float(custo_num.sum())
    return 0.0

def extrair_historico_os(df):
    """Extrai os dados para alimentar o gráfico de histórico de emissão de OS."""
    if 'Abertura' in df.columns:
        df_temp = pd.DataFrame()
        df_temp['Data'] = pd.to_datetime(df['Abertura'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Data'])
        df_temp['Ano'] = df_temp['Data'].dt.year
        df_temp['Mes'] = df_temp['Data'].dt.month
        
        historico = df_temp.groupby(['Ano', 'Mes']).size().reset_index(name='Contagem')
        return historico
    return pd.DataFrame()
