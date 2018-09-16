
devices = {
	"F0" : ["STM32F0x0", "STM32F0x1", "STM32F0x2", "STM32F0x8"],
	"F1" : ["STM32F100",  "STM32F101",  "STM32F102",  "STM32F103",  "STM32F107"],
	"F2" : ["STM32F215", "STM32F217",],
	"F3" : ["STM32F301", "STM32F302", "STM32F303", "STM32F373", "STM32F3x4", "STM32F3x8", ],
	"F4" : ["STM32F401", "STM32F405", "STM32F407", "STM32F410", "STM32F411", "STM32F412",
		 "STM32F413", "STM32F427", "STM32F429", "STM32F446", "STM32F469", ],
	"F7" : ["STM32F7x2", "STM32F7x3", "STM32F7x5", "STM32F7x6", "STM32F7x7", "STM32F7x9",],
	#"H7" : ["STM32H7x3",],
	"L0" : ["STM32L0x1", "STM32L0x2", "STM32L0x3",],
	"L1" : ["STM32L100", "STM32L151", "STM32L162",],
	"L4" : ["STM32L4x1", "STM32L4x2", "STM32L4x3", "STM32L4x5", "STM32L4x6",],
	"L4+" : ["STM32L4R5", "STM32L4R7", "STM32L4R9","STM32L4S5", "STM32L4S7", "STM32L4S9",],
	#"F103" : ["STM32F103xx_enum"],
}
devices["All"] = sum(devices.values(),[])
devices["F"] = sum([devices[k] for k in ["F0","F1","F2","F3","F4","F7"]],[])
devices["L"] = sum([devices[k] for k in ["L0","L1","L4"]],[])