"""
@file       test_sumo.py
@author     ysq
@date       2024-07-03
@brief      This is an quick tutorial of sumo script.
"""

import time
import datetime
import pandas as pd  
import dynamita.scheduler as ds
import dynamita.tool as dtool
from loguru import logger 
from pathlib import Path 
import matplotlib.pyplot as plt 
import os
import numpy as np
def msg_Callback(job, msg):
    if ds.sumo.isSimFinishedMsg(msg):  # 如果模拟完成，保存状态文件
        # job从1开始, 每次递增, 注意每次运行是4的倍数，否则会保存错位文件
        ds.sumo.sendCommand(job, f'save test.xml')
       
    if msg.startswith('530045'):  # 如果代号进行到530045，完成模拟进程
        ds.sumo.finish(job)

def data_Callback(job, data):
    jobData = ds.sumo.getJobData(job)
    jobData['data'] = data

def minutes2freqstr(minutes):  
    return f'{minutes}T'  
#检查文件夹是否存在，不存在就创建
def create_folder_if_not_exists(folder_path):  
    if not os.path.exists(folder_path):  
        os.makedirs(folder_path)
#计算MAE误差
def calculate_mae(df1, df2):  
    """计算两个 DataFrame 之间的 MAE"""  
    diff = df1.values - df2.values
    abs_diff = np.abs(diff)
    total_absolute_error = np.mean(abs_diff)
    return total_absolute_error
#绘制误差曲线
def error():
    base_file = Path(f'D:\\oyy\\sumo_code_tutorial\\sumo_code_tutorial\\2h_input_jpg\\2h_simulation_results.xlsx')  
    other_files = [  
    Path(f'D:\\oyy\\sumo_code_tutorial\\sumo_code_tutorial\\{step}h_input_jpg\\{step}h_simulation_results.xlsx')  
    for step in range(4, 13, 2)  # 生成 4h, 6h, 8h, ..., 14h 的文件路径  
]  
    error_mae = []
    for other_file in other_files:
        # 读取基准数据  
        df_base = pd.read_excel(base_file, index_col='Time', parse_dates=True)  
        df_other = pd.read_excel(other_file, index_col='Time', parse_dates=True)  
        num_rows = df_other.shape[0]
        df_base_subset = df_base.iloc[:num_rows:]
        mae = calculate_mae(df_other, df_base_subset)  
        error_mae.append(mae)
    #绘制误差图
    plt.figure(figsize=(10,6))
    plt.plot(range(4,13,2),error_mae,maker='o',linestyle='-',color = 'b')
    plt.xticks(range(4,13,2))
    plt.xlabel('Simulation Time Interval (hours)')  
    plt.ylabel('Mean Absolute Error (MAE)')  
    plt.title('Mean Absolute Error vs. Simulation Time Interval')  
    plt.grid(True)  
    plt.tight_layout()  
    plt.savefig('D:\\oyy\\sumo_code_tutorial\\sumo_code_tutorial\\mae_plot.png')  # 保存图像  
#绘制出水变量的变化曲线
def variable_jpg():
    files = [Path(f'D:\\oyy\\sumo_code_tutorial\\sumo_code_tutorial\\test1\\{step}h_input_jpg\\{step}h_simulation_results.xlsx')
    for step in range(2,15,2)]
    variables = [  
            
            'Sumo__Plant__aao_effluent_4__TN',            # 出水TN  
            'Sumo__Plant__aao_effluent_4__SNHx',          # 出水SNHx  
            'Sumo__Plant__aao_effluent_4__XTSS',          # 出水XTSS  
            'Sumo__Plant__aao_effluent_4__TCOD',          # 出水TCOD  
            'Sumo__Plant__aao_effluent_4__TP',            # 出水TP  
            'Sumo__Plant__aao_cstr7_2_2__XTSS',               # 好氧池末端XTSS  
            'Sumo__Plant__aao_cstr7_2_2__SO2'                 # 好氧池末端SO2  
        ] 
    for variable in variables:
        plt.figure(figsize=(12, 8))  # 创建新图形
        for file in files:
            df_other = pd.read_excel(file,index_col='Time',parse_dates=True)
            plt.plot(df_other.index,df_other[f'{variable}'],label=f'{file.stem}')
        # 图表美化  
        plt.xlabel('Time')  
        plt.ylabel(f'{variable}')  
        
        plt.legend()  
        plt.grid(True)  
        plt.tight_layout()  
        
        # 保存和显示图表  
        plt.savefig(f'D:\\oyy\\sumo_code_tutorial\\sumo_code_tutorial\\test1\\variable_change\\{variable}_changes_plot.png')  
        plt.close


def test():

    model_no = 4
    star_time = datetime.datetime(2024, 4, 8, 1)


    start_time = time.time()
    model = f"model/sumoproject4.3.{model_no}.dll"
    init_states = f'state/state{model_no}_{star_time.strftime("%Y-%m-%d-%H-00")}.xml'
    
    cleaning_data_path = Path('D:\oyy\sumo_code_tutorial\sumo_code_tutorial\\test1\\2024-04-08-2024-06-28_cleaning_data.xlsx')
    
    # 加载数据  
    all_cleaning_data = pd.read_excel(cleaning_data_path, parse_dates=['cleaning_time'])  

    ds.sumo.setParallelJobs(1)
    # 绑定消息回调函数
    ds.sumo.message_callback = msg_Callback
    # 绑定数据回调函数
    ds.sumo.datacomm_callback = data_Callback
    results = []
    time_points = []  
    step = 1

    for i in range(0, len(all_cleaning_data),step):
        # 4. 设定时间段内运行sumo进行模拟, 获取输出和loss
        inf_args = all_cleaning_data.iloc[i]
        
        
        # 模型输入变量
        Influ_Q1 = inf_args['influent_q1_handled'] * 24  # 进水流量, 采集数据(m3/h)到sumo(m3/d)的单位转换
        Influ_Q2 = inf_args['influent_q2_handled'] * 24  # 进水流量
        Influ_TCOD          = inf_args['influent_tcod_handled']  # 进水总COD
        Influ_TKN           = inf_args['influent_tkn_handled']  # 进水总氮
        Influ_frSNHx_TKN    = inf_args['influent_frsnhx_tkn_handled']  # 进水氨氮/进水总氮
        Influ_TP            = inf_args['influent_tp_handled']  # 进水总磷
        Influ_pH            = inf_args['influent_ph_handled']  # 进水PH
        Influ_T             = inf_args['influent_t']  # 进水温度
        variables = [  
            
            'Sumo__Plant__aao_effluent_4__TN',            # 出水TN  
            'Sumo__Plant__aao_effluent_4__SNHx',          # 出水SNHx  
            'Sumo__Plant__aao_effluent_4__XTSS',          # 出水XTSS  
            'Sumo__Plant__aao_effluent_4__TCOD',          # 出水TCOD  
            'Sumo__Plant__aao_effluent_4__TP',            # 出水TP  
            'Sumo__Plant__aao_cstr7_2_2__XTSS',               # 好氧池末端XTSS  
            'Sumo__Plant__aao_cstr7_2_2__SO2'                 # 好氧池末端SO2  
        ]  
        commands = [
                    f'set Sumo__Plant__aao_influent_2_2__param__Q {Influ_Q2 / 2}',
                    f'set Sumo__Plant__aao_influent_2_2__param__TCOD {Influ_TCOD}',
                    f'set Sumo__Plant__aao_influent_2_2__param__TKN {Influ_TKN}',
                    f'set Sumo__Plant__aao_influent_2_2__param__frSNHx_TKN {Influ_frSNHx_TKN}',
                    f'set Sumo__Plant__aao_influent_2_2__param__TP {Influ_TP}',
                    f'set Sumo__Plant__aao_influent_2_2__param__pH {Influ_pH}',
                    f'set Sumo__Plant__aao_influent_2_2__param__T {Influ_T}'
                    ]
        end_commands = [
            'maptoic',  # 映射
            f'set Sumo__StopTime {2*dtool.hour}',  # 模拟的时长
            f'set Sumo__DataComm {2*dtool.hour}',  # 通讯的间隔
            'mode dynamic',  # 设置为动态模式
            'start'  # 开始模拟
        ]
        job_list = ds.sumo.schedule(
            model=model,  # 模型文件
            commands=[f'load {init_states}',
                    *commands,
                    *end_commands
                ],
            variables=variables,
            jobData={
                'data': {},
                ds.sumo.persistent: True
            }
        )
        

        while ds.sumo.scheduledJobs > 0:
            pass
        
        data = ds.sumo.jobData[job_list]['data']
        results.append(data)  
        time_points.append(inf_args['cleaning_time'].strftime('%Y-%m-%d %H:%M:%S'))    
        
    ds.sumo.cleanup()  # 清除sumo的任务规划器
    end_time = time.time()
    execution_time = end_time - start_time
    # 将结果保存到 Exc
    df_results = pd.DataFrame(results, index=time_points)  
    df_results.index.name = 'Time'  
    # 新增一行保存执行时间  
    df_results.loc['Execution Time (seconds)'] = execution_time  
    excel_output_path = Path(f'D:\oyy\sumo_code_tutorial\sumo_code_tutorial\\test1\{step*2}h_input_jpg\\{step*2}h_simulation_results.xlsx')  
    df_results.to_excel(excel_output_path)  
            
     # 数据可视化  
    for variable in variables:  
        plt.figure(figsize=(20,12))  
        plt.plot(time_points, [result[variable] for result in results], label=variable)  
        plt.xlabel('Time')  
        plt.ylabel(variable)  
        plt.title(f'{variable} over time')  
        plt.legend()  
        plt.grid(True)  
        plt.savefig(f'D:\oyy\sumo_code_tutorial\sumo_code_tutorial\\test1\\{step*2}h_input_jpg\{variable}.png')    

     
   
 
    

if __name__ == '__main__':
    test()