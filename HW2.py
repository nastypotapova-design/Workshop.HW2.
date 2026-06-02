import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

#Создаем словарь для отчета
readme_data = {}
#-----------------------------------------------------------------------------------------------------------------------
# ЧАСТЬ1.
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК1. Отбор компаний с заполненным показателем ROE
#-----------------------------------------------------------------------------------------------------------------------
#Сохраняем имя файла и вытаскиваем данные по ROE для каждой компании поквартально
file_path = 'HW2.xlsx'
roe_df = pd.read_excel(file_path, sheet_name='quarterly_roe')

#Устанавливаем дату как индекс
roe_df['Unnamed: 0'] = pd.to_datetime(roe_df['Unnamed: 0'])
roe_df.set_index('Unnamed: 0', inplace=True)
roe_df.index.name = 'Date'

#Расчитываем количество пропусков в данном df
initial_missing = roe_df.isnull().sum().sum()

#Из-за большого числа пропусков необходимо удалить компании из списка, в которых доля пропуска более 75%.
#Остальные данные заполним из текущих - на следующих этапах.
completeness = (roe_df.notna().sum() / len(roe_df)) * 100
completeness = completeness.sort_values(ascending=False)
#Указываем долю пропусков
threshold = 25
full_companies = completeness[completeness >= threshold].index.tolist()

#Создаем новый df с компаниями, у которых более 25% данных по ROE
roe_clean = roe_df[full_companies].copy()
#Заполняем пропуски предыдущим значением
roe_clean = roe_clean.ffill()
#Если у компрании не было начальных показателей, заполняем тем, что было до
roe_clean = roe_clean.bfill()

#Расчитываем количество пропусков после удаления компаний и заполнения пропусков
final_missing = roe_clean.isnull().sum().sum()

#Определяем даты df
quarter_dates = roe_clean.index
print(roe_clean.head())
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['n_companies'] = len(full_companies)
readme_data['n_quarters'] = len(quarter_dates)
readme_data['period_start'] = quarter_dates.min().strftime('%Y-%m-%d')
readme_data['period_end'] = quarter_dates.max().strftime('%Y-%m-%d')
readme_data['roe_initial_companies'] = len(roe_df.columns)
readme_data['roe_final_companies'] = len(full_companies)
readme_data['roe_initial_missing'] = initial_missing
readme_data['roe_final_missing'] = final_missing
readme_data['roe_threshold'] = threshold
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК2. Выгрузка скорректированных цен акций компаний
#-----------------------------------------------------------------------------------------------------------------------
prices_df = pd.read_excel(file_path, sheet_name='daily_adj_close')
#Устанавливаем дату как индекс
prices_df['Date'] = pd.to_datetime(prices_df['Date'])
prices_df.set_index('Date', inplace=True)
#Оставляем те компании, которые есть в df с показателе ROE
prices_clean = prices_df[full_companies].copy()
print(prices_clean.head())

#-----------------------------------------------------------------------------------------------------------------------
# БЛОК3. Расчет доходности по кварталам, в соответсвии с датами показателя ROE
#-----------------------------------------------------------------------------------------------------------------------
quarter_dates = roe_clean.index
quarterly_returns = pd.DataFrame(index=quarter_dates, columns=full_companies)
#Отбираем список цен акций в соотвествии датой показателя.
for i, quarter_end in enumerate(quarter_dates):
    #  Выбираем цену на конец квартала: дата из показателя ROE или ближайщий торговый день
    end_candidates = prices_clean.index[prices_clean.index >= quarter_end]
    actual_end = end_candidates[0]
    end_prices = prices_clean.loc[actual_end]

    # Определим цену акции на начало квартала
    if i == 0:
        # Для первого квартала выбирается дата первая в списке (на начало января)
        actual_start = prices_clean.index[0]
    else:
        # Для остальных кварталов дата предыдущего квартала
        prev_quarter = quarter_dates[i - 1]
        start_candidates = prices_clean.index[prices_clean.index >= prev_quarter]
        actual_start = start_candidates[0]

    start_prices = prices_clean.loc[actual_start]

    # Считаем доходность для каждого квартала
    quarterly_returns.loc[quarter_end] = (end_prices / start_prices - 1)
print(quarterly_returns.head())
print(f" Всего пропусков: {quarterly_returns.isnull().sum().sum()}")
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['returns_calculation_method'] = 'End_Price / Start_Price - 1'
readme_data['returns_missing'] = quarterly_returns.isnull().sum().sum()
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК4. Выгрузка капитализации
#-----------------------------------------------------------------------------------------------------------------------
mcap_df = pd.read_excel(file_path, sheet_name='quarterly_mcap')
#Устанавливаем дату как индекс
mcap_df['Unnamed: 0'] = pd.to_datetime(mcap_df['Unnamed: 0'])
mcap_df.set_index('Unnamed: 0', inplace=True)
mcap_df.index.name = 'Date'
#Оставляем те компании, которые есть в df с показателе ROE
mcap_clean = mcap_df[full_companies].copy()
#Заполняем пропуски предыдущим значением
mcap_clean = mcap_clean.ffill()
#Если у компрании не было начальных показателей, заполняем тем, что было до
mcap_clean = mcap_clean.bfill()
print(mcap_clean.head())
print(f" Всего пропусков: {mcap_clean.isnull().sum().sum()}")
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['mcap_missing'] = mcap_clean.isnull().sum().sum()
readme_data['mcap_shape'] = mcap_clean.shape
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК5. Создаем единый df. Предварительно расчитываем среднее значение по рынку
#-----------------------------------------------------------------------------------------------------------------------
#Среднее значение доходности по всем компаниям
mean_returns = quarterly_returns.mean(axis=1).astype(float)
mean_returns.name = 'Market_Avg_Return'

#Среднее значение ROE по всем компаниям
mean_roe = roe_clean.mean(axis=1).astype(float)
mean_roe.name = 'Market_Avg_ROE'

#Среднее значение mcap по всем компаниям
mean_mcap = mcap_clean.mean(axis=1).astype(float)
mean_mcap.name = 'Market_Avg_MCap'

#Создаем общий df по рынку
time_series_df = pd.DataFrame({
    'Date': quarter_dates,
    'Market_Avg_Return': mean_returns.values,
    'Market_Avg_ROE': mean_roe.values,
    'Market_Avg_MCap': mean_mcap.values
})
print(time_series_df.head())
print(f" Всего пропусков: {time_series_df.isnull().sum().sum()}")
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['time_series_missing'] = time_series_df.isnull().sum().sum()
readme_data['time_series_shape'] = time_series_df.shape
readme_data['avg_return_mean'] = mean_returns.mean()
readme_data['avg_roe_mean'] = mean_roe.mean()
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК6. Создаем панель данных по всем компаниям
#-----------------------------------------------------------------------------------------------------------------------
panel_data_list = []
#Выбираем каждую компания из списка подходящих компаний
for company in full_companies:
    # Выбираем даты из списка дат и для каждой компании объелиняем показатели - доходность, рое, капитализацию
    for date in quarter_dates:
        roe_val = roe_clean.loc[date, company]
        ret_val = quarterly_returns.loc[date, company]
        mcap_val = mcap_clean.loc[date, company]

        panel_data_list.append({
            'Date': date,
            'Company': company,
            'Return': ret_val,
            'ROE': roe_val,
            'MarketCap': mcap_val})

panel_df = pd.DataFrame(panel_data_list)
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК7. Сохраняем данные в эксель.
#-----------------------------------------------------------------------------------------------------------------------
output_file = 'time_series.xlsx'
with pd.ExcelWriter(output_file) as writer:
    time_series_df.to_excel(writer, sheet_name='time_series', index=False)

    roe_clean.to_excel(writer, sheet_name='roe_by_company')

    quarterly_returns.to_excel(writer, sheet_name='returns_by_company')

    mcap_clean.to_excel(writer, sheet_name='mcap_by_company')

    panel_df.to_excel(writer, sheet_name='panel_data', index=False)

#-----------------------------------------------------------------------------------------------------------------------
# ЧАСТЬ2.
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК1. Расчет линейной регресии по всему рынку
#-----------------------------------------------------------------------------------------------------------------------
#Вводим переменные х и у
y = time_series_df['Market_Avg_Return']
X = sm.add_constant(time_series_df['Market_Avg_ROE'])

# Считаем линейную регресию
model = sm.OLS(y, X).fit()

#Результаты
print("\nРезультаты линейной регресии:")
print(f"Коэффициент (beta):     {model.params['Market_Avg_ROE']:.6f}")
print(f"t-statistic:            {model.tvalues['Market_Avg_ROE']:.6f}")
print(f"p-value:                {model.pvalues['Market_Avg_ROE']:.6f}")
print(f"R-squared:              {model.rsquared:.6f}")
print(f"Константа (alpha):       {model.params['const']:.6f}")
print(f"Стандартная ошибка:      {model.bse['Market_Avg_ROE']:.6f}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['ols_beta'] = model.params['Market_Avg_ROE']
readme_data['ols_t-stat'] = model.tvalues['Market_Avg_ROE']
readme_data['ols_p-value'] = model.pvalues['Market_Avg_ROE']
readme_data['ols_rsquared'] = model.rsquared
readme_data['ols_const'] = model.params['const']
readme_data['ols_std_error'] = model.bse['Market_Avg_ROE']
readme_data['ols_significant'] = 'Yes' if model.pvalues['Market_Avg_ROE'] < 0.05 else 'No'
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК2. Расчет панельной регресии без временного эффекта
#-----------------------------------------------------------------------------------------------------------------------
# Отбираем необходимые показатели для панельной регресии
panel_clean = panel_df[['Return', 'ROE', 'Company', 'Date']].copy()

# Устанавливаем индекс по двум параметрам (Company, Date)
panel_clean = panel_clean.set_index(['Company', 'Date'])

# Запускаем panel regression
panel_model = PanelOLS(
    dependent=panel_clean['Return'],
    exog=sm.add_constant(panel_clean['ROE']),
    entity_effects=True,
    time_effects=False,
    drop_absorbed=True
)

#Сохраняем результаты в переменную
panel_results = panel_model.fit(cov_type='robust')

#Результаты
print("\nРезультаты панельной регресии без временного эффекта:")
print(f"Коэффициент (beta):     {panel_results.params['ROE']:.6f}")
print(f"t-statistic:            {panel_results.tstats['ROE']:.6f}")
print(f"p-value:                {panel_results.pvalues['ROE']:.6f}")
print(f"R-squared:              {panel_results.rsquared:.6f}")
print(f"R-squared within:       {panel_results.rsquared_within:.6f}")
print(f"R-squared between:      {panel_results.rsquared_between:.6f}")
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['panel_beta'] = panel_results.params['ROE']
readme_data['panel_t-stat'] = panel_results.tstats['ROE']
readme_data['panel_p-value'] = panel_results.pvalues['ROE']
readme_data['panel_rsquared'] = panel_results.rsquared
readme_data['panel_rsquared_within'] = panel_results.rsquared_within
readme_data['panel_significant'] = 'Yes' if panel_results.pvalues['ROE'] < 0.05 else 'No'
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК3. Расчет панельной регресии с временным эффектом
#-----------------------------------------------------------------------------------------------------------------------
# Запускаем panel regression
panel_model2 = PanelOLS(
    dependent=panel_clean['Return'],
    exog=sm.add_constant(panel_clean['ROE']),
    entity_effects=True,
    time_effects=True,
    drop_absorbed=True
)

#Сохраняем результаты в переменную
panel_results_2 = panel_model2.fit(cov_type='clustered', cluster_entity=True)

#Результаты
print("\nРезультаты панельной регресии с временным эффектом:")
print(f"Коэффициент (beta):     {panel_results_2.params['ROE']:.6f}")
print(f"t-statistic:            {panel_results_2.tstats['ROE']:.6f}")
print(f"p-value:                {panel_results_2.pvalues['ROE']:.6f}")
print(f"R-squared:              {panel_results_2.rsquared:.6f}")
print(f"R-squared within:       {panel_results_2.rsquared_within:.6f}")
print(f"R-squared between:      {panel_results_2.rsquared_between:.6f}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['panel_time_beta'] = panel_results_2.params['ROE']
readme_data['panel_time_t-stat'] = panel_results_2.tstats['ROE']
readme_data['panel_time_p-value'] = panel_results_2.pvalues['ROE']
readme_data['panel_time_rsquared'] = panel_results_2.rsquared
readme_data['panel_time_significant'] = 'Yes' if panel_results_2.pvalues['ROE'] < 0.05 else 'No'
# -----------------------------------------------------------------------------------------------------------------------
# БЛОК4. Выгрузка цены акций по компаниям за последние 10 дней с YAHOO
# -----------------------------------------------------------------------------------------------------------------------
try:
    # Скачиваем данные
    recent_prices = yf.download(
        tickers=full_companies,
        period="10d",
        interval="1d",
        auto_adjust=False,
        progress=False
    )
    # Выбираем скорректированную цену акций
    recent_data = recent_prices['Adj Close']

    # Сохраняем в Excel
    recent_data.to_excel('recent_10_days_prices.xlsx')
    print(recent_data.head())

except Exception as e:
    print(f"Ошибка: {e}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['yahoo_downloaded'] = True
readme_data['yahoo_tickers_count'] = len(full_companies)
readme_data['yahoo_dates'] = f"{recent_data.index.min().strftime('%Y-%m-%d')} to {recent_data.index.max().strftime('%Y-%m-%d')}" if 'recent_data' in locals() else 'N/A'
#-----------------------------------------------------------------------------------------------------------------------
# ЧАСТЬ3.
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК1. Анализ выбросов
#-----------------------------------------------------------------------------------------------------------------------
# Функция для поиска выбросов по IQR методу
def get_outliers_info(data, column_name):
    Q1 = data[column_name].quantile(0.25) #Определяет границу 25%
    Q3 = data[column_name].quantile(0.75) #Определяет границу 75%
    IQR = Q3 - Q1 #расчитываем разницу для определения нижней и верхней границы
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = data[(data[column_name] < lower_bound) | (data[column_name] > upper_bound)] #отбираем выбросы
    return {
        'Q1': Q1,
        'Q3': Q3,
        'IQR': IQR,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'outliers_count': len(outliers),
        'outliers_pct': len(outliers) / len(data) * 100
    } #функция возвращает параметры метода для необходимого показателя


print("Анализ выбросов в доходностях (IQR метод):")
returns_info = get_outliers_info(panel_df, 'Return')
print(f"   Q1 (25й перцентиль):    {returns_info['Q1']:.4f}")
print(f"   Q3 (75й перцентиль):    {returns_info['Q3']:.4f}")
print(f"   IQR:                    {returns_info['IQR']:.4f}")
print(f"   Нижняя граница:         {returns_info['lower_bound']:.4f}")
print(f"   Верхняя граница:        {returns_info['upper_bound']:.4f}")
print(f"   Количество выбросов:    {returns_info['outliers_count']}")
print(f"   Доля выбросов:          {returns_info['outliers_pct']:.2f}%")

# Анализируем выбросы в ROE
print("Анализ выбросов в ROE (IQR метод):")
roe_info = get_outliers_info(panel_df, 'ROE')
print(f"   Q1 (25й перцентиль):    {roe_info['Q1']:.4f}")
print(f"   Q3 (75й перцентиль):    {roe_info['Q3']:.4f}")
print(f"   IQR:                    {roe_info['IQR']:.4f}")
print(f"   Нижняя граница:         {roe_info['lower_bound']:.4f}")
print(f"   Верхняя граница:        {roe_info['upper_bound']:.4f}")
print(f"   Количество выбросов:    {roe_info['outliers_count']}")
print(f"   Доля выбросов:          {roe_info['outliers_pct']:.2f}%")

# Визуализация распределения данных по двум параметрам
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Boxplot доходностей
axes[0, 0].boxplot(panel_df['Return'].dropna())
axes[0, 0].set_title('Boxplot доходностей (Return)', fontsize=12)
axes[0, 0].set_ylabel('Доходность')
axes[0, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[0, 0].grid(True, alpha=0.3)

# Гистограмма доходностей
axes[0, 1].hist(panel_df['Return'].dropna(), bins=30, edgecolor='black', alpha=0.7)
axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=1)
axes[0, 1].set_title('Распределение доходностей', fontsize=12)
axes[0, 1].set_xlabel('Доходность')
axes[0, 1].set_ylabel('Частота')
axes[0, 1].grid(True, alpha=0.3)

# Boxplot ROE
axes[1, 0].boxplot(panel_df['ROE'].dropna())
axes[1, 0].set_title('Boxplot ROE', fontsize=12)
axes[1, 0].set_ylabel('ROE')
axes[1, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[1, 0].grid(True, alpha=0.3)

# Гистограмма ROE
axes[1, 1].hist(panel_df['ROE'].dropna(), bins=30, edgecolor='black', alpha=0.7)
axes[1, 1].axvline(x=0, color='red', linestyle='--', linewidth=1)
axes[1, 1].set_title('Распределение ROE', fontsize=12)
axes[1, 1].set_xlabel('ROE')
axes[1, 1].set_ylabel('Частота')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outliers_analysis.png', dpi=100, bbox_inches='tight')
plt.close()

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['returns_outliers_count'] = returns_info['outliers_count']
readme_data['returns_outliers_pct'] = returns_info['outliers_pct']
readme_data['roe_outliers_count'] = roe_info['outliers_count']
readme_data['roe_outliers_pct'] = roe_info['outliers_pct']
readme_data['returns_lower'] = returns_info['lower_bound']
readme_data['returns_upper'] = returns_info['upper_bound']
readme_data['roe_lower'] = roe_info['lower_bound']
readme_data['roe_upper'] = roe_info['upper_bound']
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК2. Удаление выбросов
#-----------------------------------------------------------------------------------------------------------------------
#Необходимо удалить все выбросы, которые выходят за нижнююю и верхнюю границу
# Удаляем выбросы по двум параметрам по верхней и нижней границе
panel_no_outliers = panel_df[
    (panel_df['Return'] >= returns_info['lower_bound']) &
    (panel_df['Return'] <= returns_info['upper_bound']) &
    (panel_df['ROE'] >= roe_info['lower_bound']) &
    (panel_df['ROE'] <= roe_info['upper_bound'])
].copy()

# Визуализация распределения данных по двум параметрам с учетом удаленных значений
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Boxplot доходностей
axes[0, 0].boxplot(panel_no_outliers['Return'].dropna())
axes[0, 0].set_title('Boxplot доходностей (Return)', fontsize=12)
axes[0, 0].set_ylabel('Доходность')
axes[0, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[0, 0].grid(True, alpha=0.3)

# Гистограмма доходностей
axes[0, 1].hist(panel_no_outliers['Return'].dropna(), bins=30, edgecolor='black', alpha=0.7)
axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=1)
axes[0, 1].set_title('Распределение доходностей', fontsize=12)
axes[0, 1].set_xlabel('Доходность')
axes[0, 1].set_ylabel('Частота')
axes[0, 1].grid(True, alpha=0.3)

# Boxplot ROE
axes[1, 0].boxplot(panel_no_outliers['ROE'].dropna())
axes[1, 0].set_title('Boxplot ROE', fontsize=12)
axes[1, 0].set_ylabel('ROE')
axes[1, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[1, 0].grid(True, alpha=0.3)

# Гистограмма ROE
axes[1, 1].hist(panel_no_outliers['ROE'].dropna(), bins=30, edgecolor='black', alpha=0.7)
axes[1, 1].axvline(x=0, color='red', linestyle='--', linewidth=1)
axes[1, 1].set_title('Распределение ROE', fontsize=12)
axes[1, 1].set_xlabel('ROE')
axes[1, 1].set_ylabel('Частота')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('panel_without_outliers.png', dpi=100, bbox_inches='tight')
plt.close()
#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['initial_obs'] = len(panel_df)
readme_data['final_obs'] = len(panel_no_outliers)
readme_data['outliers_removed'] = len(panel_df) - len(panel_no_outliers)
readme_data['outliers_removed_pct'] = (len(panel_df) - len(panel_no_outliers)) / len(panel_df) * 100
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК3. Влияние веса капитализации компании на вклад доходностей и ROE. Сравнение.
#-----------------------------------------------------------------------------------------------------------------------
# Для каждого периода считаем суммарную капитализацию
total_mcap_by_date = panel_no_outliers.groupby('Date')['MarketCap'].sum()

# Рассчитываем вес каждой компании в каждом периоде
panel_no_outliers['Weight'] = panel_no_outliers.apply(
    lambda row: row['MarketCap'] / total_mcap_by_date[row['Date']],
    axis=1)

# Рассчитываем взвешенные показатели для каждого периода
weighted_by_period = []

for date in panel_no_outliers['Date'].unique():
    period_data = panel_no_outliers[panel_no_outliers['Date'] == date]
    #Перемножаем вес на показатель за каждую дату
    weighted_return = (period_data['Return'] * period_data['Weight']).sum()
    weighted_roe = (period_data['ROE'] * period_data['Weight']).sum()

    weighted_by_period.append({
        'Date': date,
        'Weighted_Avg_Return': weighted_return,
        'Weighted_Avg_ROE': weighted_roe,
        'N_companies': len(period_data)
    })
#Создаем новый df с учетом весов
weighted_ts_df = pd.DataFrame(weighted_by_period)
weighted_ts_df = weighted_ts_df.sort_values('Date') #сортировка по дате


# Создаем общий df со старыми средними показателями и новыми с учетом весов
comparison_df = time_series_df.merge(weighted_ts_df, on='Date', how='inner')
comparison_df = comparison_df[['Date', 'Market_Avg_Return', 'Weighted_Avg_Return',
                               'Market_Avg_ROE', 'Weighted_Avg_ROE']]

# Визуализация сравнения
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Сравнение доходностей
axes[0].plot(comparison_df['Date'], comparison_df['Market_Avg_Return'],
             'b-o', label='Простое среднее', linewidth=1.5, markersize=4)
axes[0].plot(comparison_df['Date'], comparison_df['Weighted_Avg_Return'],
             'r-s', label='Взвешенное по капитализации', linewidth=1.5, markersize=4)
axes[0].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[0].set_title('Сравнение доходностей: простое vs взвешенное среднее', fontsize=12)
axes[0].set_ylabel('Доходность')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Сравнение ROE
axes[1].plot(comparison_df['Date'], comparison_df['Market_Avg_ROE'],
             'g-o', label='Простое среднее', linewidth=1.5, markersize=4)
axes[1].plot(comparison_df['Date'], comparison_df['Weighted_Avg_ROE'],
             'm-s', label='Взвешенное по капитализации', linewidth=1.5, markersize=4)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].set_title('Сравнение ROE: простое vs взвешенное среднее', fontsize=12)
axes[1].set_ylabel('ROE')
axes[1].set_xlabel('Дата')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('weighted_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['weighted_periods'] = len(weighted_ts_df)
readme_data['weighted_return_mean'] = weighted_ts_df['Weighted_Avg_Return'].mean()
readme_data['weighted_roe_mean'] = weighted_ts_df['Weighted_Avg_ROE'].mean()
# -----------------------------------------------------------------------------------------------------------------------
# БЛОК4. Удаление пустых значений с помощью pqr.align
# -----------------------------------------------------------------------------------------------------------------------
#Преодразуем данные в таблицу короткого формата
# Wide-формат для доходностей
returns_wide = panel_no_outliers.pivot(index='Date', columns='Company', values='Return')
# Wide-формат для ROE
roe_wide = panel_no_outliers.pivot(index='Date', columns='Company', values='ROE')
try:
    import pqr
    # Применяем pqr.align (происходит сопоставление двух таблиц, по доходности и рое, в случае отсутсвия информации, остаются те данные, которые есть в двух таблицах)
    aligned_returns, aligned_roe = pqr.align(returns_wide, roe_wide)

    # Преобразуем обратно в длинный формат таблицы
    aligned_returns_long = aligned_returns.stack().reset_index()
    aligned_returns_long.columns = ['Date', 'Company', 'Return']

    aligned_roe_long = aligned_roe.stack().reset_index()
    aligned_roe_long.columns = ['Date', 'Company', 'ROE']

    # Объединяем по двум критериям
    aligned_panel = aligned_returns_long.merge(aligned_roe_long, on=['Date', 'Company'])
except:
    #К сожалению, установить pqr не получилось, поэтому делаем в ручную
    # Находим общие компании и даты
    common_companies = set(panel_no_outliers['Company'].unique())
    common_dates = set(panel_no_outliers['Date'].unique())

    # Фильтруем по дате и компаниям
    aligned_panel = panel_no_outliers[
        panel_no_outliers['Company'].isin(common_companies) &
        panel_no_outliers['Date'].isin(common_dates)
        ].copy()

    # Удаляем строки с пропусками
    aligned_panel = aligned_panel.dropna(subset=['Return', 'ROE'])


#-----------------------------------------------------------------------------------------------------------------------
# БЛОК5. Повторный расчет линейной резресии на взвешенных данных
#-----------------------------------------------------------------------------------------------------------------------

# Используем взвешенные временные ряды из weighted_ts_df
weighted_ols_df = weighted_ts_df.dropna()
#Введение переменных х и у
y_weighted = weighted_ols_df['Weighted_Avg_Return']
X_weighted = sm.add_constant(weighted_ols_df['Weighted_Avg_ROE'])
#Расчет линейной регнресии
weighted_model = sm.OLS(y_weighted, X_weighted).fit()
#Результаты
print("\nРезультаты взвешенной регрессии:")
print(f"  Коэффициент (beta):     {weighted_model.params['Weighted_Avg_ROE']:.6f}")
print(f"  t-statistic:            {weighted_model.tvalues['Weighted_Avg_ROE']:.6f}")
print(f"  p-value:                {weighted_model.pvalues['Weighted_Avg_ROE']:.6f}")
print(f"  R-squared:              {weighted_model.rsquared:.6f}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['weighted_beta'] = weighted_model.params['Weighted_Avg_ROE']
readme_data['weighted_t-stat'] = weighted_model.tvalues['Weighted_Avg_ROE']
readme_data['weighted_p-value'] = weighted_model.pvalues['Weighted_Avg_ROE']
readme_data['weighted_rsquared'] = weighted_model.rsquared
readme_data['weighted_significant'] = 'Yes' if weighted_model.pvalues['Weighted_Avg_ROE'] < 0.05 else 'No'
#-----------------------------------------------------------------------------------------------------------------------
# БЛОК6. Функция Fama-macbeth
#-----------------------------------------------------------------------------------------------------------------------
#Функция для расчета Fama-macbeth регрессии
def fama_macbeth_regression(panel_data, y_col='Return', x_col='ROE'):

    # Сross-sectional регрессии по каждому периоду
    period_results = []
    for period in panel_data['Date'].unique():
        period_data = panel_data[panel_data['Date'] == period].copy() #Отбираем данные за одну дату по всем компаниям
        period_data = period_data.dropna(subset=[y_col, x_col])
        #Задаем переменные х и у
        X = sm.add_constant(period_data[x_col])
        y = period_data[y_col]
        #Расчитываем регрессию
        model = sm.OLS(y, X).fit()
        period_results.append({
            'Date': period,
            'const': model.params['const'],
            'beta': model.params[x_col],
            'n_obs': len(period_data),
            'r_squared': model.rsquared
        })
    #Сохраняем все в новый df
    period_results_df = pd.DataFrame(period_results)

    #Среднее значение коэффициента и константы
    mean_const = period_results_df['const'].mean()
    mean_beta = period_results_df['beta'].mean()

    #Стандартное отклонение коэффициента
    std_beta = period_results_df['beta'].std()
    n_periods = len(period_results_df)
    #Стандартная ошибка среднего
    se_beta = std_beta / (n_periods ** 0.5)

    #Расчет t-статистики (условие, что стандартная ошибка не равна 0)
    t_stat_beta = mean_beta / se_beta if se_beta != 0 else np.nan

    #Расчет p-value (доп условие, что t-статистика определена)
    if not np.isnan(t_stat_beta):
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat_beta), df=n_periods - 1))
    else:
        p_value = np.nan

    #Результаты для константы
    std_const = period_results_df['const'].std()
    #Стандартная ошибка среднего
    se_const = std_const / (n_periods ** 0.5)
    #Расчет t-статистики (условие, что стандартная ошибка не равна 0)
    t_stat_const = mean_const / se_const if se_const != 0 else np.nan

    #Сохранение результатов
    results = {
        'const': {'coefficient': mean_const, 't_stat': t_stat_const},
        'beta': {'coefficient': mean_beta, 't_stat': t_stat_beta, 'p_value': p_value}
    }
    return results, period_results_df

#-----------------------------------------------------------------------------------------------------------------------
# БЛОК7. Fama-macbeth регрессия
#-----------------------------------------------------------------------------------------------------------------------
# Используем обработанную df от выбросов и после удаления пустых значений
fm_results_full, fm_periods_full = fama_macbeth_regression(aligned_panel)

#Вывод результатов
print(f"\nРезультаты Fama-MacBeth регрессии:")
print(f"  Коэффициент (beta):     {fm_results_full['beta']['coefficient']:.6f}")
print(f"  t-statistic:            {fm_results_full['beta']['t_stat']:.6f}")
print(f"  p-value:                {fm_results_full['beta']['p_value']:.6f}")
print(f"  Константа (alpha):      {fm_results_full['const']['coefficient']:.6f}")
print(f"\n  Периодов использовано:  {len(fm_periods_full)}")
print(f"  Среднее R²:             {fm_periods_full['r_squared'].mean():.4f}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['fm_beta'] = fm_results_full['beta']['coefficient']
readme_data['fm_t-stat'] = fm_results_full['beta']['t_stat']
readme_data['fm_p-value'] = fm_results_full['beta']['p_value']
readme_data['fm_const'] = fm_results_full['const']['coefficient']
readme_data['fm_n_periods'] = len(fm_periods_full)
readme_data['fm_avg_rsquared'] = fm_periods_full['r_squared'].mean()
readme_data['fm_significant'] = 'Yes' if fm_results_full['beta']['p_value'] < 0.05 else 'No'
#-----------------------------------------------------------------------------------------------------------------------
#БЛОК8. Fama-macbeth регрессия в период COVID (2020-2021)
#-----------------------------------------------------------------------------------------------------------------------
#Задаем границы периода COVID
covid_start = pd.Timestamp('2020-01-01')
covid_end = pd.Timestamp('2021-12-31')
#Отбираем из df только нужный период
covid_panel = aligned_panel[
    (aligned_panel['Date'] >= covid_start) &
    (aligned_panel['Date'] <= covid_end)
    ].copy()
#Запускаем функцию по расчету регрессии
fm_results_covid, fm_periods_covid = fama_macbeth_regression(covid_panel)
#Вывод результатов
print(f"\nРезультаты Fama-MacBeth регрессии (COVID период):")
print(f"  Коэффициент (beta):     {fm_results_covid['beta']['coefficient']:.6f}")
print(f"  t-statistic:            {fm_results_covid['beta']['t_stat']:.6f}")
print(f"  p-value:                {fm_results_covid['beta']['p_value']:.6f}")
print(f"  Константа (alpha):      {fm_results_covid['const']['coefficient']:.6f}")
print(f"\n  Периодов использовано:  {len(fm_periods_covid)}")
print(f"  Среднее R²:             {fm_periods_covid['r_squared'].mean():.4f}")

#-----------------------------------------------------------------------------------------------------------------------
#Сохранение результатов для отчета
readme_data['fm_covid_beta'] = fm_results_covid['beta']['coefficient']
readme_data['fm_covid_t-stat'] = fm_results_covid['beta']['t_stat']
readme_data['fm_covid_p-value'] = fm_results_covid['beta']['p_value']
readme_data['fm_covid_const'] = fm_results_covid['const']['coefficient']
readme_data['fm_covid_n_periods'] = len(fm_periods_covid)
readme_data['fm_covid_avg_rsquared'] = fm_periods_covid['r_squared'].mean()
readme_data['fm_covid_significant'] = 'Yes' if fm_results_covid['beta']['p_value'] < 0.05 else 'No'
#-----------------------------------------------------------------------------------------------------------------------
#БЛОК9. Создание и написание отчета в формате README файла
#-----------------------------------------------------------------------------------------------------------------------
with open('README.md', 'w', encoding='utf-8') as f:
    f.write('# ROE and Stock Returns Analysis (Fama-MacBeth Approach)\n\n')
    f.write('## 1. Data Preparation\n\n')
    f.write('### 1.1 ROE Data Cleaning\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Initial companies** | {readme_data["roe_initial_companies"]} |\n')
    f.write(
        f'| **Final companies (after {readme_data["roe_threshold"]}% completeness threshold)** | {readme_data["roe_final_companies"]} |\n')
    f.write(
        f'| **Companies removed** | {readme_data["roe_initial_companies"] - readme_data["roe_final_companies"]} |\n')
    f.write(f'| **Analysis period** | {readme_data["period_start"]} — {readme_data["period_end"]} |\n')
    f.write(f'| **Number of quarters** | {readme_data["n_quarters"]} |\n')
    f.write(f'| **Initial missing values in ROE** | {readme_data["roe_initial_missing"]} |\n')
    f.write(f'| **Final missing values** | {readme_data["roe_final_missing"]} |\n\n')
    f.write('---\n\n')
    f.write('### 1.2 Returns Calculation\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Method** | {readme_data["returns_calculation_method"]} |\n')
    f.write(f'| **Missing returns** | {readme_data["returns_missing"]} |\n\n')
    f.write('### 1.3 Market Capitalization Data\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Periods (quarters)** | {readme_data["mcap_shape"][0]} |\n')
    f.write(f'| **Companies** | {readme_data["mcap_shape"][1]} |\n')
    f.write(f'| **Missing values** | {readme_data["mcap_missing"]} |\n\n')
    f.write('### 1.4 Market Aggregates (Time Series)\n\n')
    f.write('For each quarter, we calculate the simple average across all companies:\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Number of periods** | {readme_data["time_series_shape"][0]} |\n')
    f.write(f'| **Number of series** | {readme_data["time_series_shape"][1]} |\n')
    f.write(f'| **Missing values** | {readme_data["time_series_missing"]} |\n')
    f.write(f'| **Mean Market Return (avg across periods)** | {readme_data["avg_return_mean"]:.4f} |\n')
    f.write(f'| **Mean ROE (avg across periods)** | {readme_data["avg_roe_mean"]:.4f} |\n\n')
    f.write(
        'The cleaned data was merged into a panel dataset (Company × Quarter) and exported to `time_series.xlsx`.\n\n')
    f.write('---\n\n')

    f.write('## 2. Regression Results\n\n')
    f.write('### 2.1 Time Series OLS\n\n')
    f.write('Model: `Market_Avg_Return = α + β × Market_Avg_ROE + ε`\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Coefficient (β)** | {readme_data["ols_beta"]:.4f} |\n')
    f.write(f'| **t-statistic** | {readme_data["ols_t-stat"]:.4f} |\n')
    f.write(f'| **p-value** | {readme_data["ols_p-value"]:.4f} |\n')
    f.write(f'| **R-squared** | {readme_data["ols_rsquared"]:.4f} |\n')
    f.write(f'| **Significant (p < 0.05)** | {readme_data["ols_significant"]} |\n\n')
    f.write('---\n\n')
    f.write('### 2.2 PanelOLS (without Time Effects)\n\n')
    f.write('Model with company fixed effects: `Returnᵢₜ = αᵢ + β × ROEᵢₜ + εᵢₜ`\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Coefficient (β)** | {readme_data["panel_beta"]:.4f} |\n')
    f.write(f'| **t-statistic** | {readme_data["panel_t-stat"]:.4f} |\n')
    f.write(f'| **p-value** | {readme_data["panel_p-value"]:.4f} |\n')
    f.write(f'| **R-squared** | {readme_data["panel_rsquared"]:.4f} |\n')
    f.write(f'| **Significant (p < 0.05)** | {readme_data["panel_significant"]} |\n\n')
    f.write('---\n\n')
    f.write('### 2.3 PanelOLS (with Time Effects)\n\n')
    f.write('Model with company and time fixed effects: `Returnᵢₜ = αᵢ + γₜ + β × ROEᵢₜ + εᵢₜ`\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Coefficient (β)** | {readme_data["panel_time_beta"]:.6f} |\n')
    f.write(f'| **t-statistic** | {readme_data["panel_time_t-stat"]:.6f} |\n')
    f.write(f'| **p-value** | {readme_data["panel_time_p-value"]:.6f} |\n')
    f.write(f'| **R-squared** | {readme_data["panel_time_rsquared"]:.6f} |\n')
    f.write(f'| **Significant (p < 0.05)** | {readme_data["panel_time_significant"]} |\n\n')
    f.write('---\n\n')
    f.write('### 2.4 Recent Prices from Yahoo Finance\n\n')
    f.write(
        f'Daily prices for the last 10 trading days were downloaded for {readme_data["yahoo_tickers_count"]} tickers and saved to `recent_10_days_prices.xlsx`.\n\n')
    f.write('---\n\n')

    f.write('## 3. Outlier Analysis\n\n')
    f.write(
        'Outliers were detected using the **IQR (Interquartile Range)** method, where values outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR] are considered outliers.\n\n')
    f.write('### 3.1 IQR Summary\n\n')
    f.write('| Variable | Q1 | Q3 | IQR | Lower Bound | Upper Bound | Outliers |\n')
    f.write('|----------|----|----|-----|-------------|-------------|----------|\n')
    f.write(
        f'| Returns | {returns_info["Q1"]:.4f} | {returns_info["Q3"]:.4f} | {returns_info["IQR"]:.4f} | {returns_info["lower_bound"]:.4f} | {returns_info["upper_bound"]:.4f} | {returns_info["outliers_count"]} ({returns_info["outliers_pct"]:.1f}%) |\n')
    f.write(
        f'| ROE | {roe_info["Q1"]:.4f} | {roe_info["Q3"]:.4f} | {roe_info["IQR"]:.4f} | {roe_info["lower_bound"]:.4f} | {roe_info["upper_bound"]:.4f} | {roe_info["outliers_count"]} ({roe_info["outliers_pct"]:.1f}%) |\n\n')

    f.write('### 3.2 Visualization\n\n')
    f.write(
        'The plots below show boxplots and histograms for both variables, highlighting the distribution and extreme values.\n\n')
    f.write('![Outlier Analysis](outliers_analysis.png)\n\n')
    f.write('---\n\n')
    f.write('### 3.3 Outlier Removal\n\n')
    f.write('After identifying outliers using the IQR method, observations outside the bounds were removed:\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Initial observations** | {readme_data["initial_obs"]} |\n')
    f.write(
        f'| **Outliers removed** | {readme_data["outliers_removed"]} ({readme_data["outliers_removed_pct"]:.1f}%) |\n')
    f.write(f'| **Final observations** | {readme_data["final_obs"]} |\n\n')
    f.write('### 3.4 After Removal\n\n')
    f.write('The plots below show the data distribution after outlier removal.\n\n')
    f.write('![Panel After Outlier Removal](panel_without_outliers.png)\n\n')
    f.write('---\n\n')
    f.write('## 4. Weighting by Market Capitalization\n\n')
    f.write('Each company was weighted by its market cap relative to the total market cap for each period:\n\n')
    f.write('```\nWeightᵢₜ = MarketCapᵢₜ / ΣMarketCapₜ\n```\n\n')
    f.write('| Metric | Simple Average | Weighted Average |\n')
    f.write('|--------|----------------|------------------|\n')
    f.write(f'| **Mean Return** | {readme_data["avg_return_mean"]:.4f} | {readme_data["weighted_return_mean"]:.4f} |\n')
    f.write(f'| **Mean ROE** | {readme_data["avg_roe_mean"]:.4f} | {readme_data["weighted_roe_mean"]:.4f} |\n\n')
    f.write('![Weighted Comparison](weighted_comparison.png)\n\n')
    f.write('---\n\n')
    f.write('## 5. Weighted Regression Results\n\n')
    f.write('After weighting by market capitalization, the OLS regression was repeated:\n\n')
    f.write('| Metric | Simple OLS | Weighted OLS |\n')
    f.write('|--------|------------|--------------|\n')
    f.write(f'| **Coefficient (β)** | {readme_data["ols_beta"]:.4f} | {readme_data["weighted_beta"]:.4f} |\n')
    f.write(f'| **t-statistic** | {readme_data["ols_t-stat"]:.2f} | {readme_data["weighted_t-stat"]:.2f} |\n')
    f.write(f'| **p-value** | {readme_data["ols_p-value"]:.3f} | {readme_data["weighted_p-value"]:.3f} |\n')
    f.write(f'| **R-squared** | {readme_data["ols_rsquared"]:.3f} | {readme_data["weighted_rsquared"]:.3f} |\n')
    f.write(f'| **Significant** | {readme_data["ols_significant"]} | {readme_data["weighted_significant"]} |\n\n')

    if abs(readme_data["weighted_beta"]) > abs(readme_data["ols_beta"]):
        f.write(
            'The coefficient increased after weighting, indicating that larger companies have a stronger ROE-return relationship.\n\n')
    else:
        f.write(
            'The coefficient decreased after weighting, indicating that smaller companies have a stronger ROE-return relationship.\n\n')

    f.write('---\n\n')
    f.write('## 6. Fama-MacBeth Regression\n\n')
    f.write('The Fama-MacBeth two-step procedure:\n')
    f.write('1. Cross-sectional regression for each period: `Returnᵢ = αₜ + βₜ × ROEᵢ + εᵢ`\n')
    f.write('2. Time-series average of coefficients: `β̄ = (1/T) × Σβₜ`\n\n')

    f.write('### 6.1 Full Period Results\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Coefficient (β̄)** | {readme_data["fm_beta"]:.6f} |\n')
    f.write(f'| **t-statistic** | {readme_data["fm_t-stat"]:.6f} |\n')
    f.write(f'| **p-value** | {readme_data["fm_p-value"]:.6f} |\n')
    f.write(f'| **Significant (p < 0.05)** | {readme_data["fm_significant"]} |\n')
    f.write(f'| **Number of periods** | {readme_data["fm_n_periods"]} |\n')
    f.write(f'| **Average R²** | {readme_data["fm_avg_rsquared"]:.4f} |\n\n')

    f.write('### 6.2 Comparison of All Methods\n\n')
    f.write('| Method | Coefficient | p-value | Significant |\n')
    f.write('|--------|-------------|---------|-------------|\n')
    f.write(
        f'| OLS (Time Series) | {readme_data["ols_beta"]:.4f} | {readme_data["ols_p-value"]:.3f} | {readme_data["ols_significant"]} |\n')
    f.write(
        f'| PanelOLS (no time) | {readme_data["panel_beta"]:.4f} | {readme_data["panel_p-value"]:.3f} | {readme_data["panel_significant"]} |\n')
    f.write(
        f'| PanelOLS (with time) | {readme_data["panel_time_beta"]:.4f} | {readme_data["panel_time_p-value"]:.3f} | {readme_data["panel_time_significant"]} |\n')
    f.write(
        f'| Weighted OLS | {readme_data["weighted_beta"]:.4f} | {readme_data["weighted_p-value"]:.3f} | {readme_data["weighted_significant"]} |\n')
    f.write(
        f'| **Fama-MacBeth** | **{readme_data["fm_beta"]:.4f}** | **{readme_data["fm_p-value"]:.3f}** | **{readme_data["fm_significant"]}** |\n\n')
    f.write('**Key Observations:**\n\n')
    f.write('- Only the **Fama-MacBeth** method shows a statistically significant relationship (p < 0.05)\n')
    f.write(
        f'- The coefficient from Fama-MacBeth (β = {readme_data["fm_beta"]:.4f}) is higher than simple OLS (β = {readme_data["ols_beta"]:.4f})\n')
    f.write('- PanelOLS with time effects gives slightly higher coefficient than without time effects\n')
    f.write('- Weighting by market capitalization increased the coefficient but did not improve significance\n\n')

    f.write('**Why Fama-MacBeth differs from PanelOLS?**\n\n')
    f.write('| Aspect | PanelOLS | Fama-MacBeth |\n')
    f.write('|--------|----------|--------------|\n')
    f.write('| Coefficient | Single β for all periods | Average of period-specific βₜ |\n')
    f.write('| Period weighting | Periods with higher variance get more weight | Each period gets equal weight |\n')
    f.write('| Standard errors | Based on pooled data (clustered) | Based on time-series variation of βₜ |\n\n')

    f.write('---\n\n')
    f.write('### 6.3 COVID-19 Period (2020-2021)\n\n')
    f.write('| Metric | Value |\n')
    f.write('|--------|-------|\n')
    f.write(f'| **Coefficient (β̄)** | {readme_data["fm_covid_beta"]:.6f} |\n')
    f.write(f'| **t-statistic** | {readme_data["fm_covid_t-stat"]:.6f} |\n')
    f.write(f'| **p-value** | {readme_data["fm_covid_p-value"]:.6f} |\n')
    f.write(f'| **Significant (p < 0.05)** | {readme_data["fm_covid_significant"]} |\n')
    f.write(f'| **Number of periods** | {readme_data["fm_covid_n_periods"]} |\n')
    f.write(f'| **Average R²** | {readme_data["fm_covid_avg_rsquared"]:.4f} |\n\n')

    f.write('### 6.4 Comparison: Full Period vs COVID Period\n\n')
    f.write('| Period | Coefficient | p-value | Significant |\n')
    f.write('|--------|-------------|---------|-------------|\n')
    f.write(
        f'| Full Period | {readme_data["fm_beta"]:.4f} | {readme_data["fm_p-value"]:.3f} | {readme_data["fm_significant"]} |\n')
    f.write(
        f'| COVID-19 | {readme_data["fm_covid_beta"]:.4f} | {readme_data["fm_covid_p-value"]:.3f} | {readme_data["fm_covid_significant"]} |\n\n')

    if abs(readme_data["fm_covid_beta"]) < abs(readme_data["fm_beta"]):
        f.write('The relationship between ROE and stock returns weakened during the COVID-19 pandemic.\n\n')
    else:
        f.write('The relationship between ROE and stock returns strengthened during the COVID-19 pandemic.\n\n')

    f.write('**Possible reasons for COVID-19 period results:**\n\n')
    f.write('- Market irrationality and panic selling during the pandemic\n')
    f.write('- Government stimulus programs distorting normal market mechanisms\n')
    f.write('- High volatility making it difficult to detect fundamental relationships\n')
    f.write('- Limited number of observations (only 8 quarters)\n\n')

    f.write('---\n\n')


