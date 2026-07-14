# ADDR_DFF AST Extraction

- source_label: `1c34428d8b913963c4971d093b1a7c2df97a2509:sram_compiler/subcircuits/time_generate.py`
- addr_dff:
```json
{
  "class_name": "ADDR_DFF",
  "name_assignment": "ADDR_DFF",
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "5e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "2.5e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "num_rows",
        "kind": "positional",
        "default_source": "16"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      }
    ],
    "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=5e-07, nmos_width=2.5e-07,\n                 length=0.05e-6,num_rows=16,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,\n                 ):\n        self.num_rows = num_rows\n        n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1\n        # 动态生成节点：包括所有地址输入、输出\n        nodes = ['VDD', 'VSS', 'CLK']\n        # 添加地址输入节点 A0, A1, A2, ..\n        nodes.extend([f'A{i}' for i in range(n_bits)])\n        # 添加地址输出节点 Q0, Q1, Q2, ...\n        nodes.extend([f'A_dff{i}' for i in range(n_bits)]) \n        self.NODES = nodes\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        ) \n        n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1\n        self.dff_addr = dff(nmos_model, pmos_model)\n        self.subcircuit(self.dff_addr)\n         # 构建地址DFF阵列\n        self.add_addr_dff_array(n_bits)"
  },
  "self_num_rows_source": "num_rows",
  "n_bits_expressions": [
    "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
    "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1"
  ],
  "nodes_initial_value": [
    "VDD",
    "VSS",
    "CLK"
  ],
  "nodes_extend_expressions": [
    "[f'A{i}' for i in range(n_bits)]",
    "[f'A_dff{i}' for i in range(n_bits)]"
  ],
  "self_nodes_source": "nodes",
  "dff_addr_constructor": {
    "source_text": "self.dff_addr = dff(nmos_model, pmos_model)",
    "positional_arguments": [
      "nmos_model",
      "pmos_model"
    ],
    "keyword_arguments": {}
  },
  "subcircuit_call_source": "self.subcircuit(self.dff_addr)",
  "add_addr_dff_array_call": {
    "source_text": "self.add_addr_dff_array(n_bits)",
    "arguments": [
      "n_bits"
    ]
  },
  "add_addr_dff_array": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "n_bits",
        "kind": "positional",
        "default_source": null
      }
    ],
    "loop_target": "i",
    "loop_iterator": "range(n_bits)",
    "self_x_instance_name_expression": "f'dff_{i}'",
    "self_x_child_expression": "self.dff_addr.NAME",
    "self_x_net_argument_order": [
      "'VDD'",
      "'VSS'",
      "f'A{i}'",
      "f'A_dff{i}'",
      "'CLK'"
    ]
  }
}
```
- time:
```json
{
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "2.7e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "1.8e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "num_rows",
        "kind": "positional",
        "default_source": "16"
      },
      {
        "parameter": "num_cols",
        "kind": "positional",
        "default_source": "8"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      },
      {
        "parameter": "operation",
        "kind": "positional",
        "default_source": "'read'"
      }
    ],
    "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=0.27e-6, nmos_width=0.18e-6,\n                 length=0.05e-6,num_rows=16,num_cols=8,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,operation='read'\n                 ):\n        # 计算需要的地址位数\n        n_bits = ceil(log2(num_rows)) if num_rows > 1 else 1\n         # 动态生成节点\n        nodes = ['VDD', 'VSS', 'clk', 'csb', 'web', 'clk_buf', 'clk_bar', \n                'cs_bar','cs', 'we_bar','we','gated_clk_bar', 'gated_clk_buf', 'wl_en']\n        \n        # 添加地址输入输出节点\n        nodes.extend([f'A{i}' for i in range(n_bits)])\n        nodes.extend([f'A_dff{i}' for i in range(n_bits)])\n        if operation == 'write' or operation == 'read&write':\n            # 添加数据输入输出节点\n            nodes.extend([f'DIN{i}' for i in range(num_cols)])\n            nodes.extend([f'DIN_dff{i}' for i in range(num_cols)])\n\n        nodes += ['rbl','rbl_delay','rbl_delay_bar','s_en','w_en','PRE']\n        self.NODES = nodes\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        )\n        self.num_rows=num_rows\n        self.num_cols=num_cols\n        self.n_bits = n_bits\n        #触发器在时钟上升沿触发地址信号\n        dff_buf_addr=ADDR_DFF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",num_rows=self.num_rows)\n        self.subcircuit(dff_buf_addr)\n            # 构建地址DFF连接列表\n        addr_dff_connections = ['VDD', 'VSS', 'clk_buf']  # 基本连接\n            # 添加地址输入连接\n        for i in range(self.n_bits):\n            addr_dff_connections.append(f'A{i}')\n            # 添加地址输出连接\n        for i in range(self.n_bits):\n            addr_dff_connections.append(f'A_dff{i}')\n            # 实例化DFF\n        self.X('dff_buf_addr',\n               dff_buf_addr.NAME, *addr_dff_connections)\n\n        if operation == 'write' or operation == 'read&write':\n            #触发器在时钟上升沿触发数据信号\n            dff_buf_data=DATA_DFF(nmos_model=\"NMOS_VTG\",\n                pmos_model=\"PMOS_VTG\",num_cols=self.num_cols)  # 对于16x8结构，有8位数据\n            self.subcircuit(dff_buf_data)\n            \n            # 构建数据DFF连接列表\n            data_dff_connections = ['VDD', 'VSS', 'clk_buf']  # 基本连接\n            # 添加数据输入连接\n            for i in range(self.num_cols):  \n                data_dff_connections.append(f'DIN{i}')\n            # 添加数据输出连接\n            for i in range(self.num_cols):  \n                data_dff_connections.append(f'DIN_dff{i}')\n            # 实例化DFF\n            self.X('dff_buf_data',\n                dff_buf_data.NAME, *data_dff_connections)\n\n\n        #产生内部时钟\n        # 让 clkbuf 按实际 DFF 负载自动放大\n        ref_rows = 16\n        ref_cols = 16\n        ref_bits = ceil(log2(ref_rows))\n\n        clk_dff_count = self.n_bits + 2  # 地址DFF + CS_DFF + WE_DFF\n        ref_dff_count = ref_bits + 2\n\n        if operation == 'write' or operation == 'read&write':\n            clk_dff_count += self.num_cols\n            ref_dff_count += ref_cols\n\n        clk_drive_scale = max(1.0, clk_dff_count / ref_dff_count)\n\n        clkbuf = pdrive(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",\n            drive_scale=clk_drive_scale\n        )\n        self.subcircuit(clkbuf)\n        self.X('clkbuf',\n               clkbuf.NAME,\n               'VDD', 'VSS', 'clk', 'clk_buf')\n        #产生内部主时钟的反信号\n        inv_clk_bar = Pinv(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",\n            nmos_width=0.09e-6,\n            pmos_width=0.27e-6,\n            length=0.05e-6,\n        )\n        self.subcircuit(inv_clk_bar)\n        self.X('inv_clk_bar',\n               inv_clk_bar.NAME,\n               'VDD', 'VSS', 'clk_buf', 'clk_bar')\n        #触发器在时钟上升沿触发片选信号\n        dff_buf=DFF_BUF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\")\n        self.subcircuit(dff_buf)\n        self.X('dff_buf',\n               dff_buf.NAME,\n               'VDD', 'VSS', 'csb', 'cs_bar','cs','clk_buf')\n        #触发器在时钟上升沿触发写信号\n        dff_buf1=DFF_BUF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\")\n        self.subcircuit(dff_buf1)\n        self.X('dff_buf1',\n               dff_buf1.NAME,\n               'VDD', 'VSS', 'web', 'we_bar','we','clk_buf')\n        #门控时钟（反相）\n        and2_gated_clk_bar=AND2(nmos_model_nand=\"NMOS_VTG\",\n                                pmos_model_nand=\"PMOS_VTG\",\n                                nmos_model_inv=\"NMOS_VTG\",\n                                pmos_model_inv=\"PMOS_VTG\",\n                                nand_pmos_width=0.27e-6,\n                                nand_nmos_width=0.18e-6,\n                                inv_pmos_width=1.62e-6,\n                                inv_nmos_width=0.54e-6,\n                                length=0.05e-6,\n                                w_rc=w_rc\n                                )\n        self.subcircuit(and2_gated_clk_bar)\n        self.X('and2_gated_clk_bar',\n            and2_gated_clk_bar.NAME,\n            'VDD', 'VSS', 'cs', 'clk_bar','gated_clk_bar')\n        #门控时钟\n        and2_gated_clk_buf=AND2(nmos_model_nand=\"NMOS_VTG\",\n                                pmos_model_nand=\"PMOS_VTG\",\n                                nmos_model_inv=\"NMOS_VTG\",\n                                pmos_model_inv=\"PMOS_VTG\",\n                                nand_pmos_width=0.27e-6,\n                                nand_nmos_width=0.18e-6,\n                                inv_pmos_width=1.62e-6,\n                                inv_nmos_width=0.54e-6,\n                                length=0.05e-6,\n                                w_rc=w_rc\n                                )\n        self.subcircuit(and2_gated_clk_buf)\n        self.X('and2_gated_clk_buf',\n               and2_gated_clk_buf.NAME,\n               'VDD', 'VSS', 'cs', 'clk_buf','gated_clk_buf')\n        #字线使能，在clk的低电平\n        wl_en=wl_pdrive()\n        self.subcircuit(wl_en)\n        self.X('wl_en',\n               wl_en.NAME,\n               'VDD', 'VSS', 'gated_clk_bar', 'wl_en')\n        inv_wl_en_bar = Pinv(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",\n            nmos_width=0.09e-6,\n            pmos_width=0.27e-6,\n            length=0.05e-6,\n            num='_wl_en_bar'\n        )\n        self.subcircuit(inv_wl_en_bar)\n        self.X('inv_wl_en_bar',\n            inv_wl_en_bar.NAME,\n            'VDD', 'VSS', 'wl_en', 'wl_en_bar')\n\n        #复制位线延迟链\n        delaychain=DelayChain()\n        self.subcircuit(delaychain)\n        self.X('delaychain',\n               delaychain.NAME,\n               'VDD', 'VSS', 'rbl', 'rbl_delay')\n        #复制位线延迟反相\n        inv_rbl_delay_bar = Pinv(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",\n            nmos_width=0.09e-6,\n            pmos_width=0.27e-6,\n            length=0.05e-6,\n        )\n        self.subcircuit(inv_rbl_delay_bar)\n        self.X('inv_rbl_delay_bar',\n               inv_rbl_delay_bar.NAME,\n               'VDD', 'VSS', 'rbl_delay', 'rbl_delay_bar')\n        \n        w_en_rbl_input = 'rbl_delay_bar'\n\n        if operation == 'write' and self.num_rows == 16 and self.num_cols == 512:\n            wen_delaychain = WenDelayChain(stages=6, loads_per_stage=4, w_rc=w_rc)\n            self.subcircuit(wen_delaychain)\n            self.X('wen_delaychain',\n                wen_delaychain.NAME,\n                'VDD', 'VSS', 'rbl_delay_bar', 'rbl_delay_bar_wen')\n            w_en_rbl_input = 'rbl_delay_bar_wen'\n        #产生写使能\n        w_en_ref_cols = 64\n        w_en_scale = max(1, ceil(self.num_cols / w_en_ref_cols))#按列数放大驱动晶体管尺寸\n        w_en=AND3(nmos_model_nand=\"NMOS_VTG\",\n                pmos_model_nand=\"PMOS_VTG\",\n                nmos_model_inv=\"NMOS_VTG\",\n                pmos_model_inv=\"PMOS_VTG\",\n                nand_pmos_width=0.27e-6,\n                nand_nmos_width=0.18e-6,\n                inv_pmos_width=1.08e-6 * w_en_scale,\n                inv_nmos_width=0.36e-6 * w_en_scale,\n                length=0.05e-6,\n                w_rc=w_rc\n                )\n        self.subcircuit(w_en)\n        self.X('w_en',\n               w_en.NAME,\n               'VDD','VSS' , w_en_rbl_input , 'gated_clk_bar' ,'we', 'w_en' )\n        #产生灵敏放大器\n        s_en=AND3(nmos_model_nand=\"NMOS_VTG\",\n                pmos_model_nand=\"PMOS_VTG\",\n                nmos_model_inv=\"NMOS_VTG\",\n                pmos_model_inv=\"PMOS_VTG\",\n                nand_pmos_width=0.27e-6,\n                nand_nmos_width=0.18e-6,\n                inv_pmos_width=1.08e-6 * w_en_scale,\n                inv_nmos_width=0.36e-6 * w_en_scale,\n                length=0.05e-6,\n                w_rc=w_rc\n            )\n        self.subcircuit(s_en)\n        self.X('s_en',\n               s_en.NAME,\n               'VDD','VSS' ,'rbl_delay', 'gated_clk_bar' ,'we_bar' ,'s_en' )\n\n        #产生预充电使能\n        # pre_unbuf=PNAND2(nmos_model=\"NMOS_VTG\",\n        #                 pmos_model=\"PMOS_VTG\",\n        #                 nmos_width=0.18e-6,\n        #                 pmos_width=0.27e-6,\n        #                 length=0.05e-6,\n        #                 w_rc=w_rc\n        #                 )\n        # self.subcircuit(pre_unbuf)\n        # self.X('pre_unbuf',\n        #        pre_unbuf.NAME,\n        #        'VDD','VSS', 'gated_clk_buf', 'rbl_delay', 'PRE_UNBUF')\n\n        pre_unbuf = PNAND3(nmos_model=\"NMOS_VTG\",\n                   pmos_model=\"PMOS_VTG\",\n                   nmos_width=0.27e-6,\n                   pmos_width=0.27e-6,\n                   length=0.05e-6,\n                   w_rc=w_rc\n                   )\n        self.subcircuit(pre_unbuf)\n        self.X('pre_unbuf',\n            pre_unbuf.NAME,\n            'VDD', 'VSS', 'gated_clk_buf', 'rbl_delay', 'wl_en_bar', 'PRE_UNBUF')\n\n        \n        pre_ref_cols = 64\n        pre_col_scale = (self.num_cols + 1) / (pre_ref_cols + 1)\n        pre_pmos_scale = max(0.5, self.num_rows / 16)\n        pre_drive_scale = max(1, ceil(pre_col_scale * pre_pmos_scale))\n        pre = pdrive2_for_pre(drive_scale=pre_drive_scale)\n        self.subcircuit(pre)\n        self.X('pre',\n               pre.NAME,\n               'VDD','VSS', 'PRE_UNBUF', 'PRE')"
  },
  "addr_dff_constructor_call": {
    "source_text": "dff_buf_addr=ADDR_DFF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",num_rows=self.num_rows)",
    "positional_arguments": [],
    "keyword_arguments": {
      "nmos_model": "\"NMOS_VTG\"",
      "pmos_model": "\"PMOS_VTG\"",
      "num_rows": "self.num_rows"
    }
  },
  "addr_dff_connections_initial": [
    "VDD",
    "VSS",
    "clk_buf"
  ],
  "addr_dff_connection_loops": [
    {
      "loop_target": "i",
      "loop_iterator": "range(self.n_bits)",
      "append_expressions": [
        "f'A{i}'"
      ]
    },
    {
      "loop_target": "i",
      "loop_iterator": "range(self.n_bits)",
      "append_expressions": [
        "f'A_dff{i}'"
      ]
    }
  ],
  "dff_buf_addr_instance_call": {
    "instance_name_expression": "'dff_buf_addr'",
    "child_expression": "dff_buf_addr.NAME",
    "remaining_arguments": [
      "*addr_dff_connections"
    ]
  }
}
```
- dff:
```json
{
  "__init__": {
    "formal_parameters": [
      {
        "parameter": "self",
        "kind": "positional",
        "default_source": null
      },
      {
        "parameter": "nmos_model",
        "kind": "positional",
        "default_source": "'NMOS_VTG'"
      },
      {
        "parameter": "pmos_model",
        "kind": "positional",
        "default_source": "'PMOS_VTG'"
      },
      {
        "parameter": "pmos_width",
        "kind": "positional",
        "default_source": "5e-07"
      },
      {
        "parameter": "nmos_width",
        "kind": "positional",
        "default_source": "2.5e-07"
      },
      {
        "parameter": "length",
        "kind": "positional",
        "default_source": "5e-08"
      },
      {
        "parameter": "w_rc",
        "kind": "positional",
        "default_source": "False"
      },
      {
        "parameter": "pi_res",
        "kind": "positional",
        "default_source": "100 @ u_Ohm"
      },
      {
        "parameter": "pi_cap",
        "kind": "positional",
        "default_source": "0.001 @ u_pF"
      }
    ],
    "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=5e-07, nmos_width=2.5e-07,\n                 length=0.05e-6,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,\n                 ):\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        ) \n        self.inv_dff = Pinv(nmos_model,pmos_model,2.5e-07, 5e-07,0.05e-6,num=1)\n        self.subcircuit(self.inv_dff)\n\n        self.trans_dff = TransmissionGate(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\"\n        )\n        self.subcircuit(self.trans_dff)\n        # 构建传输门型触发器\n        self.add_dff()"
  }
}
```
