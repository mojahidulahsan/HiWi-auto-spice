from src.netlist_params import parameters
from src.gauss_var import gauss_dist
import numpy as np

class netlist_design(parameters):

	def __init__(self):
		parameters.__init__(self)
		if self.memristor_model == "JART_VCM_1b_det":  
			self.memristor_paramseters = " T0=T0 eps=esp epsphib=epsphib phiBn0=phiBn0 phin=phin un=un Nplug=Nplug \ \n a=a ny0=ny0 dWa=dWa Rth0=Rth0 Ninit=Ndiscmin rdet=rdet lcell=lcell \ \n ldet=ldet Rtheff_scaling=Rtheff_scaling RseriesTiOx=RseriesTiOx R0=R0 \ \n"
			self.variablity = "Ndiscmax={} Ndiscmin={} rdet={} ldet={}" 
		else:    
			self.memristor_paramseters = " eps=eps epsphib=epsphib phibn0=phibn0 phin=phin \ \n un=un Ninit=Ndiscmin Nplug=Nplug a=a \ \n nyo=nyo dWa=dWa Rth0=Rth0 rdet=rdet  \ \n lcell=lcell ldet=ldet Rtheff_scaling=Rtheff_scaling RTiOx=RTiOx R0=R0 \ \n Rthline=90471.5 alphaline=0.00392 eps_eff=(eps)*(8.85419e-12) \ \n epsphib_eff=(epsphib)*(8.85419e-12)"
			self.variablity = " Ndiscmax={} Ndiscmin={} lnew = {} rnew= {} " 

	def design_voltage_sources(self):

		num_volt_source = 0
		voltages_name = ""
		vpulse = "V{} ({} {}) vsource type={} val0={} val1={} period={} width={} rise={} fall={} \n" 
		voltage_source = ""
		for i in range(self.rows):
			voltages_name += "r{} ".format(i)
			voltage_source += vpulse.format(str(num_volt_source),"r{} ".format(i),0, self.input_type_r[i], self.volt_0_r[i],self.volt_1_r[i], self.time_period_r[i], self.pulse_width_r[i], self.rise_time_r[i],self.fall_time_r[i])
			num_volt_source += 1
		for j in range(self.columns):
			voltages_name += f"c{j} "
			voltage_source += vpulse.format(str(num_volt_source),"c{} ".format(j),0, self.input_type_c[j], self.volt_0_c[j],self.volt_1_c[j], self.time_period_c[j], self.pulse_width_c[j], self.rise_time_c[j],self.fall_time_c[j])
			num_volt_source += 1
		return voltages_name,voltage_source


	def update_param(self, mean_sigma_param = {}, bools_var = {}):

		var_param = "parameters "
		d_to_d_vardict = {}
		gauss = gauss_dist((self.rows,self.columns))

		for variation in bools_var:
			if bools_var[variation]:
				d_to_d_vardict[variation] = gauss_dist(mean_sigma_param[variation]).create_distribution((self.rows,self.columns))

		
		if(len(d_to_d_vardict) == 0):
			print("No random variations.\n")
		else:
			var_param += gauss.make_paramset(d_to_d_vardict) 
			print(f"{len(d_to_d_vardict)} parameters are updated due to variation.\n")
	
		
		return var_param


	def create_pulse(self, step_time, pulse_vol, time_unit, WL_pulse, SEL_voltage, BL_voltage, row, column):

		insert_p = False
		concatenated = False

		start_time_b = 0
		stop_time_b = 3*step_time

		if not WL_pulse[row]:
			if not any(WL_pulse):
				start_time = 0
				stop_time = 3 * step_time
				
			else:
				max_start_time = 0
				for p in WL_pulse:
					if p:
						s_time = int(p[-2][:-1])+1
						if s_time > max_start_time : max_start_time = s_time
				
				
				start_time = max_start_time
				stop_time = start_time + step_time * 3

		
		else:
			start_time = int(WL_pulse[row][-2][:-1])+1 
			stop_time = start_time + step_time * 2
			concatenated = True

		
		for i in range(start_time, stop_time, step_time):

			if insert_p == False and concatenated == False:
				WL_pulse[row].append(str(i)+time_unit)
				WL_pulse[row].append('0')
				WL_pulse[row].append(str(i+(step_time-1))+time_unit)
				WL_pulse[row].append('0')

				
				for k in range(0, self.columns):
						BL_voltage[k].append(str(i)+time_unit)
						BL_voltage[k].append("0")
						BL_voltage[k].append(str(i+(step_time-1))+time_unit)
						BL_voltage[k].append("0")  
				
				for k in range(0, self.rows):
						SEL_voltage[k].append(str(i)+time_unit)
						SEL_voltage[k].append("0")
						SEL_voltage[k].append(str(i+(step_time-1))+time_unit)
						SEL_voltage[k].append("0")

				
				insert_p = True		

			else:
				WL_pulse[row].append(str(i)+time_unit)
				WL_pulse[row].append(pulse_vol)
				WL_pulse[row].append(str(i+(step_time-1))+time_unit)
				WL_pulse[row].append(pulse_vol)

				SEL_voltage[row].append(str(i)+time_unit)
				SEL_voltage[row].append("Gate_V")
				SEL_voltage[row].append(str(i+(step_time-1))+time_unit)
				SEL_voltage[row].append("Gate_V")

							
				BL_voltage[column].append(str(i)+time_unit)
				BL_voltage[column].append("0")
				BL_voltage[column].append(str(i+(step_time-1))+time_unit)
				BL_voltage[column].append("0")

				for k in range(0, self.columns):
					if k != column:
						BL_voltage[k].append(str(i)+time_unit)
						BL_voltage[k].append(pulse_vol)
						BL_voltage[k].append(str(i+(step_time-1))+time_unit)
						BL_voltage[k].append(pulse_vol)  

				insert_p = False
				concatenated = False



	def pulses_to_string(self,in_pulses_list):

		WL_pulses = [[] for _ in range(self.rows)]
		SEL_voltage = [[] for _ in range(self.rows)]
		BL_voltage = [[] for _ in range(self.columns)]


		for s in in_pulses_list:

			row,column = int(s[1]), int(s[2])

			if s[0].lower() == "read":
				self.create_pulse(self.step_time, "Read_V", self.time_units, WL_pulses, SEL_voltage, BL_voltage, row, column)
				
			elif s[0].lower() == "set":
				self.create_pulse(self.step_time, "Set_V", self.time_units, WL_pulses, SEL_voltage, BL_voltage, row, column)

			elif s[0].lower() == "reset":
				self.create_pulse(self.step_time, "Reset_V", self.time_units, WL_pulses, SEL_voltage, BL_voltage, row, column)
			
		if not WL_pulses:
			print("Empty list!")
			return
		
		
		pulses_str = ""
		c = 0
		for i in range(0, self.rows):
			pulses_str += f"V_WL{i}(r{i} 0) vsource type=pwl wave=[\\\n"
			for k in range(0, len(WL_pulses[i])-1, 2):
				pulses_str += WL_pulses[i][k] + '\t' + WL_pulses[i][k+1] + '\t\\\n'
			pulses_str += ']\n'

			pulses_str += f"V_SEL{i}(g{i} 0) vsource type=pwl wave=[\\\n"
			for k in range(0, len(SEL_voltage[i])-1, 2):
				pulses_str += SEL_voltage[i][k] + '\t' + SEL_voltage[i][k+1] + '\t\\\n'
			pulses_str += ']\n\n'


		pulses_str += "\n\n"
		for j in range(0, self.columns):
			pulses_str += f"V_BL{j}(c{j} 0) vsource type=pwl wave=[\\\n"
			for k in range(0, len(BL_voltage[j])-1, 2):
				pulses_str += BL_voltage[j][k] + '\t' + BL_voltage[j][k+1] + '\t\\\n'
			pulses_str += ']\n\n'
			
		
		return pulses_str

	def pulses_to_file(self, row_list, filename):

		if not row_list:
			print("Empty list")
			return
		
		with open(filename,'w') as fl:
			for s in row_list:
				cmd = s[0]
				row = s[1]

				if cmd.lower() == "w":
					for i in range(2, len(s)):
						if s[i] == '0':
							fl.write(f"Reset,{row},{i-2}\n")
						elif s[i] == '1':
							fl.write(f"Set,{row},{i-2}\n")

				elif cmd.lower() == "r":
					for i in range(2, len(s)):
						if s[i] == '1':
							fl.write(f"Read,{row},{i-2}\n")


	def sweep_to_string(self, sweep_params):

		sweep_str = ""
		min_g, max_g, step_g = sweep_params[0], sweep_params[1], sweep_params[2]

		if max_g < min_g : step_g = -step_g
		
		sweep_str += "swp sweep param = Gate_V values=["
		for i in np.arange(min_g, max_g, step_g):
			sweep_str += str(np.round(i,2)) + " "

		sweep_str = sweep_str[0:-1] + f"]{{\n\ttran tran stop = {self.simulation_stop_time} errpreset=conservative maxstep={self.simulation_maxstep}\n}}"

		return sweep_str


	def gen_netlist(self,memristor_params= {}, pulses = [], sweep_params = [], file_name = "", memristor_model_path = "", transistor_model_path = ""):

		print("Generating netlist...\n")
		
		str_param = ""
		str_ckt = ""
		str_instances = ""
		str_pulses = ""

		str_param += "global 0\n"
		str_param += "ahdl_include " + "\"" + memristor_model_path + "\"" + "\n"
		str_param += "include " + "\"" + transistor_model_path + "\"" + "\n" 
		str_param += f"simulatorOptions options vabstol = {self.vabstol} iabstol = {self.iabstol} temp = {self.temp} tnom = {self.tnom} gmin = {self.gmin}\n"
		str_param += f"trans {self.simulation_type} stop = {self.simulation_stop_time} maxstep = {self.simulation_maxstep} errpreset=conservative\n"
		str_param += f"saveOptions options save=all currents=all saveahdlvars=all\n"
		str_param += f"parameters Read_V = {self.read_v} Set_V = {self.set_v} Reset_V = {self.reset_v} Gate_V = {self.gate_v} Transistor_Width = {self.trans_width}n Transistor_Length = {self.trans_length}n\n"
		if memristor_params: str_param += "parameters " + self.parameters_list(param=memristor_params) + "\n"
		str_param += "\n"

		str_ckt += "subckt XBAR_CELL WordLine BitLine Select_Line\n"
		str_ckt += f"\tM0 (net WordLine) {self.memristor_model}"
		str_ckt += "\t" + self.parameters_list(param=memristor_params, numerical_mode = False) + "\n"
		str_ckt += f"\tT0 (net Select_Line BitLine BitLine) {self.transistor_model}  w = Transistor_Width	 l = Transistor_Length\n"
		str_ckt += "ends XBAR_CELL\n\n"

		k = 0
		for i in range(0, self.rows):
			for j in range(0, self.columns):
				str_instances += f"I{k} (r{i} c{j} g{i}) XBAR_CELL\n"
				k += 1

		str_pulses += "\n\n" + self.pulses_to_string(pulses)
		#str_pulses += "\nV1 (c0  0) vsource dc=0\n\n\n"


		if sweep_params:
			str_pulses += self.sweep_to_string(sweep_params)


		to_be_written = str_param + str_ckt + str_instances + str_pulses
		file_ = open(file_name,"w")
		file_.write(to_be_written)
		print(f"Netlist, model path and simulation parameters written to \"{file_name}\"\n")
		