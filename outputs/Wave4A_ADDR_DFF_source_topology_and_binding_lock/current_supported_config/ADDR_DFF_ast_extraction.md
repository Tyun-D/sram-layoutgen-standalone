# ADDR_DFF AST Extraction

- snapshot_path: `/data1/qujh/work/sram_layoutgen_step45_clean/outputs/Wave4A_ADDR_DFF_source_topology_and_binding_lock/current_supported_config/source/time_generate_locked_1c34428.py`
- addr_dff:
```json
{
  "class_lineno": 405,
  "class_end_lineno": 441,
  "class_ast_dump": "ClassDef(\n  name='ADDR_DFF',\n  bases=[\n    Name(id='BaseSubcircuit', ctx=Load())],\n  keywords=[],\n  body=[\n    Expr(\n      value=Constant(value='D Flip-Flop for address')),\n    Assign(\n      targets=[\n        Name(id='NAME', ctx=Store())],\n      value=Constant(value='ADDR_DFF')),\n    FunctionDef(\n      name='__init__',\n      args=arguments(\n        posonlyargs=[],\n        args=[\n          arg(arg='self'),\n          arg(arg='nmos_model'),\n          arg(arg='pmos_model'),\n          arg(arg='pmos_width'),\n          arg(arg='nmos_width'),\n          arg(arg='length'),\n          arg(arg='num_rows'),\n          arg(arg='w_rc'),\n          arg(arg='pi_res'),\n          arg(arg='pi_cap')],\n        kwonlyargs=[],\n        kw_defaults=[],\n        defaults=[\n          Constant(value='NMOS_VTG'),\n          Constant(value='PMOS_VTG'),\n          Constant(value=5e-07),\n          Constant(value=2.5e-07),\n          Constant(value=5e-08),\n          Constant(value=16),\n          Constant(value=False),\n          BinOp(\n            left=Constant(value=100),\n            op=MatMult(),\n            right=Name(id='u_Ohm', ctx=Load())),\n          BinOp(\n            left=Constant(value=0.001),\n            op=MatMult(),\n            right=Name(id='u_pF', ctx=Load()))]),\n      body=[\n        Assign(\n          targets=[\n            Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='num_rows',\n              ctx=Store())],\n          value=Name(id='num_rows', ctx=Load())),\n        Assign(\n          targets=[\n            Name(id='n_bits', ctx=Store())],\n          value=IfExp(\n            test=Compare(\n              left=Attribute(\n                value=Name(id='self', ctx=Load()),\n                attr='num_rows',\n                ctx=Load()),\n              ops=[\n                Gt()],\n              comparators=[\n                Constant(value=1)]),\n            body=Call(\n              func=Name(id='ceil', ctx=Load()),\n              args=[\n                Call(\n                  func=Name(id='log2', ctx=Load()),\n                  args=[\n                    Attribute(\n                      value=Name(id='self', ctx=Load()),\n                      attr='num_rows',\n                      ctx=Load())],\n                  keywords=[])],\n              keywords=[]),\n            orelse=Constant(value=1))),\n        Assign(\n          targets=[\n            Name(id='nodes', ctx=Store())],\n          value=List(\n            elts=[\n              Constant(value='VDD'),\n              Constant(value='VSS'),\n              Constant(value='CLK')],\n            ctx=Load())),\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Name(id='nodes', ctx=Load()),\n              attr='extend',\n              ctx=Load()),\n            args=[\n              ListComp(\n                elt=JoinedStr(\n                  values=[\n                    Constant(value='A'),\n                    FormattedValue(\n                      value=Name(id='i', ctx=Load()),\n                      conversion=-1)]),\n                generators=[\n                  comprehension(\n                    target=Name(id='i', ctx=Store()),\n                    iter=Call(\n                      func=Name(id='range', ctx=Load()),\n                      args=[\n                        Name(id='n_bits', ctx=Load())],\n                      keywords=[]),\n                    ifs=[],\n                    is_async=0)])],\n            keywords=[])),\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Name(id='nodes', ctx=Load()),\n              attr='extend',\n              ctx=Load()),\n            args=[\n              ListComp(\n                elt=JoinedStr(\n                  values=[\n                    Constant(value='A_dff'),\n                    FormattedValue(\n                      value=Name(id='i', ctx=Load()),\n                      conversion=-1)]),\n                generators=[\n                  comprehension(\n                    target=Name(id='i', ctx=Store()),\n                    iter=Call(\n                      func=Name(id='range', ctx=Load()),\n                      args=[\n                        Name(id='n_bits', ctx=Load())],\n                      keywords=[]),\n                    ifs=[],\n                    is_async=0)])],\n            keywords=[])),\n        Assign(\n          targets=[\n            Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='NODES',\n              ctx=Store())],\n          value=Name(id='nodes', ctx=Load())),\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Call(\n                func=Name(id='super', ctx=Load()),\n                args=[],\n                keywords=[]),\n              attr='__init__',\n              ctx=Load()),\n            args=[\n              Name(id='nmos_model', ctx=Load()),\n              Name(id='pmos_model', ctx=Load()),\n              Name(id='nmos_width', ctx=Load()),\n              Name(id='pmos_width', ctx=Load()),\n              Name(id='length', ctx=Load())],\n            keywords=[\n              keyword(\n                arg='w_rc',\n                value=Name(id='w_rc', ctx=Load())),\n              keyword(\n                arg='pi_res',\n                value=Name(id='pi_res', ctx=Load())),\n              keyword(\n                arg='pi_cap',\n                value=Name(id='pi_cap', ctx=Load()))])),\n        Assign(\n          targets=[\n            Name(id='n_bits', ctx=Store())],\n          value=IfExp(\n            test=Compare(\n              left=Attribute(\n                value=Name(id='self', ctx=Load()),\n                attr='num_rows',\n                ctx=Load()),\n              ops=[\n                Gt()],\n              comparators=[\n                Constant(value=1)]),\n            body=Call(\n              func=Name(id='ceil', ctx=Load()),\n              args=[\n                Call(\n                  func=Name(id='log2', ctx=Load()),\n                  args=[\n                    Attribute(\n                      value=Name(id='self', ctx=Load()),\n                      attr='num_rows',\n                      ctx=Load())],\n                  keywords=[])],\n              keywords=[]),\n            orelse=Constant(value=1))),\n        Assign(\n          targets=[\n            Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='dff_addr',\n              ctx=Store())],\n          value=Call(\n            func=Name(id='dff', ctx=Load()),\n            args=[\n              Name(id='nmos_model', ctx=Load()),\n              Name(id='pmos_model', ctx=Load())],\n            keywords=[])),\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='subcircuit',\n              ctx=Load()),\n            args=[\n              Attribute(\n                value=Name(id='self', ctx=Load()),\n                attr='dff_addr',\n                ctx=Load())],\n            keywords=[])),\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='add_addr_dff_array',\n              ctx=Load()),\n            args=[\n              Name(id='n_bits', ctx=Load())],\n            keywords=[]))],\n      decorator_list=[]),\n    FunctionDef(\n      name='add_addr_dff_array',\n      args=arguments(\n        posonlyargs=[],\n        args=[\n          arg(arg='self'),\n          arg(arg='n_bits')],\n        kwonlyargs=[],\n        kw_defaults=[],\n        defaults=[]),\n      body=[\n        For(\n          target=Name(id='i', ctx=Store()),\n          iter=Call(\n            func=Name(id='range', ctx=Load()),\n            args=[\n              Name(id='n_bits', ctx=Load())],\n            keywords=[]),\n          body=[\n            Expr(\n              value=Call(\n                func=Attribute(\n                  value=Name(id='self', ctx=Load()),\n                  attr='X',\n                  ctx=Load()),\n                args=[\n                  JoinedStr(\n                    values=[\n                      Constant(value='dff_'),\n                      FormattedValue(\n                        value=Name(id='i', ctx=Load()),\n                        conversion=-1)]),\n                  Attribute(\n                    value=Attribute(\n                      value=Name(id='self', ctx=Load()),\n                      attr='dff_addr',\n                      ctx=Load()),\n                    attr='NAME',\n                    ctx=Load()),\n                  Constant(value='VDD'),\n                  Constant(value='VSS'),\n                  JoinedStr(\n                    values=[\n                      Constant(value='A'),\n                      FormattedValue(\n                        value=Name(id='i', ctx=Load()),\n                        conversion=-1)]),\n                  JoinedStr(\n                    values=[\n                      Constant(value='A_dff'),\n                      FormattedValue(\n                        value=Name(id='i', ctx=Load()),\n                        conversion=-1)]),\n                  Constant(value='CLK')],\n                keywords=[]))],\n          orelse=[])],\n      decorator_list=[])],\n  decorator_list=[])",
  "name_assignment": {
    "lineno": 407,
    "source_text": "NAME = \"ADDR_DFF\"",
    "ast_dump": "Assign(\n  targets=[\n    Name(id='NAME', ctx=Store())],\n  value=Constant(value='ADDR_DFF'))",
    "normalized_value": "ADDR_DFF"
  },
  "__init__": {
    "lineno": 410,
    "end_lineno": 435,
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
    "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=5e-07, nmos_width=2.5e-07,\n                 length=0.05e-6,num_rows=16,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,\n                 ):\n        self.num_rows = num_rows\n        n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1\n        # 动态生成节点：包括所有地址输入、输出\n        nodes = ['VDD', 'VSS', 'CLK']\n        # 添加地址输入节点 A0, A1, A2, ..\n        nodes.extend([f'A{i}' for i in range(n_bits)])\n        # 添加地址输出节点 Q0, Q1, Q2, ...\n        nodes.extend([f'A_dff{i}' for i in range(n_bits)]) \n        self.NODES = nodes\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        ) \n        n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1\n        self.dff_addr = dff(nmos_model, pmos_model)\n        self.subcircuit(self.dff_addr)\n         # 构建地址DFF阵列\n        self.add_addr_dff_array(n_bits)",
    "ast_dump": "FunctionDef(\n  name='__init__',\n  args=arguments(\n    posonlyargs=[],\n    args=[\n      arg(arg='self'),\n      arg(arg='nmos_model'),\n      arg(arg='pmos_model'),\n      arg(arg='pmos_width'),\n      arg(arg='nmos_width'),\n      arg(arg='length'),\n      arg(arg='num_rows'),\n      arg(arg='w_rc'),\n      arg(arg='pi_res'),\n      arg(arg='pi_cap')],\n    kwonlyargs=[],\n    kw_defaults=[],\n    defaults=[\n      Constant(value='NMOS_VTG'),\n      Constant(value='PMOS_VTG'),\n      Constant(value=5e-07),\n      Constant(value=2.5e-07),\n      Constant(value=5e-08),\n      Constant(value=16),\n      Constant(value=False),\n      BinOp(\n        left=Constant(value=100),\n        op=MatMult(),\n        right=Name(id='u_Ohm', ctx=Load())),\n      BinOp(\n        left=Constant(value=0.001),\n        op=MatMult(),\n        right=Name(id='u_pF', ctx=Load()))]),\n  body=[\n    Assign(\n      targets=[\n        Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='num_rows',\n          ctx=Store())],\n      value=Name(id='num_rows', ctx=Load())),\n    Assign(\n      targets=[\n        Name(id='n_bits', ctx=Store())],\n      value=IfExp(\n        test=Compare(\n          left=Attribute(\n            value=Name(id='self', ctx=Load()),\n            attr='num_rows',\n            ctx=Load()),\n          ops=[\n            Gt()],\n          comparators=[\n            Constant(value=1)]),\n        body=Call(\n          func=Name(id='ceil', ctx=Load()),\n          args=[\n            Call(\n              func=Name(id='log2', ctx=Load()),\n              args=[\n                Attribute(\n                  value=Name(id='self', ctx=Load()),\n                  attr='num_rows',\n                  ctx=Load())],\n              keywords=[])],\n          keywords=[]),\n        orelse=Constant(value=1))),\n    Assign(\n      targets=[\n        Name(id='nodes', ctx=Store())],\n      value=List(\n        elts=[\n          Constant(value='VDD'),\n          Constant(value='VSS'),\n          Constant(value='CLK')],\n        ctx=Load())),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='nodes', ctx=Load()),\n          attr='extend',\n          ctx=Load()),\n        args=[\n          ListComp(\n            elt=JoinedStr(\n              values=[\n                Constant(value='A'),\n                FormattedValue(\n                  value=Name(id='i', ctx=Load()),\n                  conversion=-1)]),\n            generators=[\n              comprehension(\n                target=Name(id='i', ctx=Store()),\n                iter=Call(\n                  func=Name(id='range', ctx=Load()),\n                  args=[\n                    Name(id='n_bits', ctx=Load())],\n                  keywords=[]),\n                ifs=[],\n                is_async=0)])],\n        keywords=[])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='nodes', ctx=Load()),\n          attr='extend',\n          ctx=Load()),\n        args=[\n          ListComp(\n            elt=JoinedStr(\n              values=[\n                Constant(value='A_dff'),\n                FormattedValue(\n                  value=Name(id='i', ctx=Load()),\n                  conversion=-1)]),\n            generators=[\n              comprehension(\n                target=Name(id='i', ctx=Store()),\n                iter=Call(\n                  func=Name(id='range', ctx=Load()),\n                  args=[\n                    Name(id='n_bits', ctx=Load())],\n                  keywords=[]),\n                ifs=[],\n                is_async=0)])],\n        keywords=[])),\n    Assign(\n      targets=[\n        Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='NODES',\n          ctx=Store())],\n      value=Name(id='nodes', ctx=Load())),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Call(\n            func=Name(id='super', ctx=Load()),\n            args=[],\n            keywords=[]),\n          attr='__init__',\n          ctx=Load()),\n        args=[\n          Name(id='nmos_model', ctx=Load()),\n          Name(id='pmos_model', ctx=Load()),\n          Name(id='nmos_width', ctx=Load()),\n          Name(id='pmos_width', ctx=Load()),\n          Name(id='length', ctx=Load())],\n        keywords=[\n          keyword(\n            arg='w_rc',\n            value=Name(id='w_rc', ctx=Load())),\n          keyword(\n            arg='pi_res',\n            value=Name(id='pi_res', ctx=Load())),\n          keyword(\n            arg='pi_cap',\n            value=Name(id='pi_cap', ctx=Load()))])),\n    Assign(\n      targets=[\n        Name(id='n_bits', ctx=Store())],\n      value=IfExp(\n        test=Compare(\n          left=Attribute(\n            value=Name(id='self', ctx=Load()),\n            attr='num_rows',\n            ctx=Load()),\n          ops=[\n            Gt()],\n          comparators=[\n            Constant(value=1)]),\n        body=Call(\n          func=Name(id='ceil', ctx=Load()),\n          args=[\n            Call(\n              func=Name(id='log2', ctx=Load()),\n              args=[\n                Attribute(\n                  value=Name(id='self', ctx=Load()),\n                  attr='num_rows',\n                  ctx=Load())],\n              keywords=[])],\n          keywords=[]),\n        orelse=Constant(value=1))),\n    Assign(\n      targets=[\n        Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='dff_addr',\n          ctx=Store())],\n      value=Call(\n        func=Name(id='dff', ctx=Load()),\n        args=[\n          Name(id='nmos_model', ctx=Load()),\n          Name(id='pmos_model', ctx=Load())],\n        keywords=[])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='subcircuit',\n          ctx=Load()),\n        args=[\n          Attribute(\n            value=Name(id='self', ctx=Load()),\n            attr='dff_addr',\n            ctx=Load())],\n        keywords=[])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='add_addr_dff_array',\n          ctx=Load()),\n        args=[\n          Name(id='n_bits', ctx=Load())],\n        keywords=[]))],\n  decorator_list=[])"
  },
  "self_num_rows_assignment": {
    "lineno": 416,
    "source_text": "self.num_rows = num_rows",
    "ast_dump": "Assign(\n  targets=[\n    Attribute(\n      value=Name(id='self', ctx=Load()),\n      attr='num_rows',\n      ctx=Store())],\n  value=Name(id='num_rows', ctx=Load()))",
    "normalized_source": "num_rows"
  },
  "n_bits_assignments": [
    {
      "lineno": 417,
      "source_text": "n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
      "ast_dump": "Assign(\n  targets=[\n    Name(id='n_bits', ctx=Store())],\n  value=IfExp(\n    test=Compare(\n      left=Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='num_rows',\n        ctx=Load()),\n      ops=[\n        Gt()],\n      comparators=[\n        Constant(value=1)]),\n    body=Call(\n      func=Name(id='ceil', ctx=Load()),\n      args=[\n        Call(\n          func=Name(id='log2', ctx=Load()),\n          args=[\n            Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='num_rows',\n              ctx=Load())],\n          keywords=[])],\n      keywords=[]),\n    orelse=Constant(value=1)))",
      "normalized_expression": "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1"
    },
    {
      "lineno": 431,
      "source_text": "n_bits = ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
      "ast_dump": "Assign(\n  targets=[\n    Name(id='n_bits', ctx=Store())],\n  value=IfExp(\n    test=Compare(\n      left=Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='num_rows',\n        ctx=Load()),\n      ops=[\n        Gt()],\n      comparators=[\n        Constant(value=1)]),\n    body=Call(\n      func=Name(id='ceil', ctx=Load()),\n      args=[\n        Call(\n          func=Name(id='log2', ctx=Load()),\n          args=[\n            Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='num_rows',\n              ctx=Load())],\n          keywords=[])],\n      keywords=[]),\n    orelse=Constant(value=1)))",
      "normalized_expression": "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1"
    }
  ],
  "nodes_initial_list": {
    "lineno": 419,
    "source_text": "nodes = ['VDD', 'VSS', 'CLK']",
    "ast_dump": "Assign(\n  targets=[\n    Name(id='nodes', ctx=Store())],\n  value=List(\n    elts=[\n      Constant(value='VDD'),\n      Constant(value='VSS'),\n      Constant(value='CLK')],\n    ctx=Load()))",
    "normalized_value": [
      "VDD",
      "VSS",
      "CLK"
    ]
  },
  "nodes_extend_calls": [
    {
      "lineno": 421,
      "source_text": "nodes.extend([f'A{i}' for i in range(n_bits)])",
      "ast_dump": "Expr(\n  value=Call(\n    func=Attribute(\n      value=Name(id='nodes', ctx=Load()),\n      attr='extend',\n      ctx=Load()),\n    args=[\n      ListComp(\n        elt=JoinedStr(\n          values=[\n            Constant(value='A'),\n            FormattedValue(\n              value=Name(id='i', ctx=Load()),\n              conversion=-1)]),\n        generators=[\n          comprehension(\n            target=Name(id='i', ctx=Store()),\n            iter=Call(\n              func=Name(id='range', ctx=Load()),\n              args=[\n                Name(id='n_bits', ctx=Load())],\n              keywords=[]),\n            ifs=[],\n            is_async=0)])],\n    keywords=[]))",
      "normalized_expression": "[f'A{i}' for i in range(n_bits)]"
    },
    {
      "lineno": 423,
      "source_text": "nodes.extend([f'A_dff{i}' for i in range(n_bits)])",
      "ast_dump": "Expr(\n  value=Call(\n    func=Attribute(\n      value=Name(id='nodes', ctx=Load()),\n      attr='extend',\n      ctx=Load()),\n    args=[\n      ListComp(\n        elt=JoinedStr(\n          values=[\n            Constant(value='A_dff'),\n            FormattedValue(\n              value=Name(id='i', ctx=Load()),\n              conversion=-1)]),\n        generators=[\n          comprehension(\n            target=Name(id='i', ctx=Store()),\n            iter=Call(\n              func=Name(id='range', ctx=Load()),\n              args=[\n                Name(id='n_bits', ctx=Load())],\n              keywords=[]),\n            ifs=[],\n            is_async=0)])],\n    keywords=[]))",
      "normalized_expression": "[f'A_dff{i}' for i in range(n_bits)]"
    }
  ],
  "self_nodes_assignment": {
    "lineno": 424,
    "source_text": "self.NODES = nodes",
    "ast_dump": "Assign(\n  targets=[\n    Attribute(\n      value=Name(id='self', ctx=Load()),\n      attr='NODES',\n      ctx=Store())],\n  value=Name(id='nodes', ctx=Load()))"
  },
  "dff_addr_constructor": {
    "lineno": 432,
    "source_text": "self.dff_addr = dff(nmos_model, pmos_model)",
    "ast_dump": "Assign(\n  targets=[\n    Attribute(\n      value=Name(id='self', ctx=Load()),\n      attr='dff_addr',\n      ctx=Store())],\n  value=Call(\n    func=Name(id='dff', ctx=Load()),\n    args=[\n      Name(id='nmos_model', ctx=Load()),\n      Name(id='pmos_model', ctx=Load())],\n    keywords=[]))",
    "call_positional_arguments": [
      "nmos_model",
      "pmos_model"
    ],
    "call_keyword_arguments": {}
  },
  "subcircuit_call": {
    "lineno": 433,
    "source_text": "self.subcircuit(self.dff_addr)",
    "ast_dump": "Expr(\n  value=Call(\n    func=Attribute(\n      value=Name(id='self', ctx=Load()),\n      attr='subcircuit',\n      ctx=Load()),\n    args=[\n      Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='dff_addr',\n        ctx=Load())],\n    keywords=[]))"
  },
  "add_addr_dff_array_call": {
    "lineno": 435,
    "source_text": "self.add_addr_dff_array(n_bits)",
    "ast_dump": "Expr(\n  value=Call(\n    func=Attribute(\n      value=Name(id='self', ctx=Load()),\n      attr='add_addr_dff_array',\n      ctx=Load()),\n    args=[\n      Name(id='n_bits', ctx=Load())],\n    keywords=[]))",
    "normalized_argument": "n_bits"
  },
  "add_addr_dff_array": {
    "lineno": 437,
    "end_lineno": 441,
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
    "source_text": "def add_addr_dff_array(self, n_bits):\n        # 创建DFF和反相器\n        for i in range(n_bits):\n            self.X(f'dff_{i}', self.dff_addr.NAME, \n                   'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK')",
    "ast_dump": "FunctionDef(\n  name='add_addr_dff_array',\n  args=arguments(\n    posonlyargs=[],\n    args=[\n      arg(arg='self'),\n      arg(arg='n_bits')],\n    kwonlyargs=[],\n    kw_defaults=[],\n    defaults=[]),\n  body=[\n    For(\n      target=Name(id='i', ctx=Store()),\n      iter=Call(\n        func=Name(id='range', ctx=Load()),\n        args=[\n          Name(id='n_bits', ctx=Load())],\n        keywords=[]),\n      body=[\n        Expr(\n          value=Call(\n            func=Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='X',\n              ctx=Load()),\n            args=[\n              JoinedStr(\n                values=[\n                  Constant(value='dff_'),\n                  FormattedValue(\n                    value=Name(id='i', ctx=Load()),\n                    conversion=-1)]),\n              Attribute(\n                value=Attribute(\n                  value=Name(id='self', ctx=Load()),\n                  attr='dff_addr',\n                  ctx=Load()),\n                attr='NAME',\n                ctx=Load()),\n              Constant(value='VDD'),\n              Constant(value='VSS'),\n              JoinedStr(\n                values=[\n                  Constant(value='A'),\n                  FormattedValue(\n                    value=Name(id='i', ctx=Load()),\n                    conversion=-1)]),\n              JoinedStr(\n                values=[\n                  Constant(value='A_dff'),\n                  FormattedValue(\n                    value=Name(id='i', ctx=Load()),\n                    conversion=-1)]),\n              Constant(value='CLK')],\n            keywords=[]))],\n      orelse=[])],\n  decorator_list=[])",
    "loop": {
      "lineno": 439,
      "source_text": "for i in range(n_bits):\n            self.X(f'dff_{i}', self.dff_addr.NAME, \n                   'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK')",
      "ast_dump": "For(\n  target=Name(id='i', ctx=Store()),\n  iter=Call(\n    func=Name(id='range', ctx=Load()),\n    args=[\n      Name(id='n_bits', ctx=Load())],\n    keywords=[]),\n  body=[\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='X',\n          ctx=Load()),\n        args=[\n          JoinedStr(\n            values=[\n              Constant(value='dff_'),\n              FormattedValue(\n                value=Name(id='i', ctx=Load()),\n                conversion=-1)]),\n          Attribute(\n            value=Attribute(\n              value=Name(id='self', ctx=Load()),\n              attr='dff_addr',\n              ctx=Load()),\n            attr='NAME',\n            ctx=Load()),\n          Constant(value='VDD'),\n          Constant(value='VSS'),\n          JoinedStr(\n            values=[\n              Constant(value='A'),\n              FormattedValue(\n                value=Name(id='i', ctx=Load()),\n                conversion=-1)]),\n          JoinedStr(\n            values=[\n              Constant(value='A_dff'),\n              FormattedValue(\n                value=Name(id='i', ctx=Load()),\n                conversion=-1)]),\n          Constant(value='CLK')],\n        keywords=[]))],\n  orelse=[])",
      "iterator_expression": "range(n_bits)",
      "target_expression": "i"
    },
    "self_X": {
      "lineno": 440,
      "source_text": "self.X(f'dff_{i}', self.dff_addr.NAME, \n                   'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK')",
      "ast_dump": "Call(\n  func=Attribute(\n    value=Name(id='self', ctx=Load()),\n    attr='X',\n    ctx=Load()),\n  args=[\n    JoinedStr(\n      values=[\n        Constant(value='dff_'),\n        FormattedValue(\n          value=Name(id='i', ctx=Load()),\n          conversion=-1)]),\n    Attribute(\n      value=Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='dff_addr',\n        ctx=Load()),\n      attr='NAME',\n      ctx=Load()),\n    Constant(value='VDD'),\n    Constant(value='VSS'),\n    JoinedStr(\n      values=[\n        Constant(value='A'),\n        FormattedValue(\n          value=Name(id='i', ctx=Load()),\n          conversion=-1)]),\n    JoinedStr(\n      values=[\n        Constant(value='A_dff'),\n        FormattedValue(\n          value=Name(id='i', ctx=Load()),\n          conversion=-1)]),\n    Constant(value='CLK')],\n  keywords=[])",
      "instance_name_expression": "f'dff_{i}'",
      "child_cell_expression": "self.dff_addr.NAME",
      "net_argument_order": [
        "'VDD'",
        "'VSS'",
        "f'A{i}'",
        "f'A_dff{i}'",
        "'CLK'"
      ],
      "keyword_arguments": {}
    }
  }
}
```
- time_addr_usage:
```json
{
  "time_init_lineno": 492,
  "addr_dff_constructor_call": {
    "lineno": 524,
    "source_text": "dff_buf_addr=ADDR_DFF(nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\",num_rows=self.num_rows)",
    "ast_dump": "Assign(\n  targets=[\n    Name(id='dff_buf_addr', ctx=Store())],\n  value=Call(\n    func=Name(id='ADDR_DFF', ctx=Load()),\n    args=[],\n    keywords=[\n      keyword(\n        arg='nmos_model',\n        value=Constant(value='NMOS_VTG')),\n      keyword(\n        arg='pmos_model',\n        value=Constant(value='PMOS_VTG')),\n      keyword(\n        arg='num_rows',\n        value=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='num_rows',\n          ctx=Load()))]))",
    "positional_arguments": [],
    "keyword_arguments": {
      "nmos_model": "\"NMOS_VTG\"",
      "pmos_model": "\"PMOS_VTG\"",
      "num_rows": "self.num_rows"
    }
  },
  "addr_dff_connections_initial": {
    "lineno": 528,
    "source_text": "addr_dff_connections = ['VDD', 'VSS', 'clk_buf']",
    "ast_dump": "Assign(\n  targets=[\n    Name(id='addr_dff_connections', ctx=Store())],\n  value=List(\n    elts=[\n      Constant(value='VDD'),\n      Constant(value='VSS'),\n      Constant(value='clk_buf')],\n    ctx=Load()))",
    "normalized_value": [
      "VDD",
      "VSS",
      "clk_buf"
    ]
  },
  "addr_dff_connection_loops": [
    {
      "lineno": 530,
      "source_text": "for i in range(self.n_bits):\n            addr_dff_connections.append(f'A{i}')",
      "ast_dump": "For(\n  target=Name(id='i', ctx=Store()),\n  iter=Call(\n    func=Name(id='range', ctx=Load()),\n    args=[\n      Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='n_bits',\n        ctx=Load())],\n    keywords=[]),\n  body=[\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='addr_dff_connections', ctx=Load()),\n          attr='append',\n          ctx=Load()),\n        args=[\n          JoinedStr(\n            values=[\n              Constant(value='A'),\n              FormattedValue(\n                value=Name(id='i', ctx=Load()),\n                conversion=-1)])],\n        keywords=[]))],\n  orelse=[])",
      "iterator_expression": "range(self.n_bits)"
    },
    {
      "lineno": 533,
      "source_text": "for i in range(self.n_bits):\n            addr_dff_connections.append(f'A_dff{i}')",
      "ast_dump": "For(\n  target=Name(id='i', ctx=Store()),\n  iter=Call(\n    func=Name(id='range', ctx=Load()),\n    args=[\n      Attribute(\n        value=Name(id='self', ctx=Load()),\n        attr='n_bits',\n        ctx=Load())],\n    keywords=[]),\n  body=[\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='addr_dff_connections', ctx=Load()),\n          attr='append',\n          ctx=Load()),\n        args=[\n          JoinedStr(\n            values=[\n              Constant(value='A_dff'),\n              FormattedValue(\n                value=Name(id='i', ctx=Load()),\n                conversion=-1)])],\n        keywords=[]))],\n  orelse=[])",
      "iterator_expression": "range(self.n_bits)"
    }
  ],
  "dff_buf_addr_instance_call": {
    "lineno": 536,
    "source_text": "self.X('dff_buf_addr',\n               dff_buf_addr.NAME, *addr_dff_connections)",
    "ast_dump": "Call(\n  func=Attribute(\n    value=Name(id='self', ctx=Load()),\n    attr='X',\n    ctx=Load()),\n  args=[\n    Constant(value='dff_buf_addr'),\n    Attribute(\n      value=Name(id='dff_buf_addr', ctx=Load()),\n      attr='NAME',\n      ctx=Load()),\n    Starred(\n      value=Name(id='addr_dff_connections', ctx=Load()),\n      ctx=Load())],\n  keywords=[])",
    "instance_name_expression": "'dff_buf_addr'",
    "child_cell_expression": "dff_buf_addr.NAME",
    "remaining_arguments": [
      "*addr_dff_connections"
    ],
    "keyword_arguments": {}
  }
}
```
- dff_constructor_defaults:
```json
{
  "lineno": 190,
  "source_text": "def __init__(self, nmos_model=\"NMOS_VTG\", pmos_model=\"PMOS_VTG\",\n                 # Base widths for NAND gate transistors\n                 pmos_width=5e-07, nmos_width=2.5e-07,\n                 length=0.05e-6,\n                 w_rc=False, pi_res=100 @ u_Ohm, pi_cap=0.001 @ u_pF,\n                 ):\n\n        super().__init__(\n            nmos_model, pmos_model,\n            nmos_width, pmos_width, length,\n            w_rc=w_rc, pi_res=pi_res, pi_cap=pi_cap,\n        ) \n        self.inv_dff = Pinv(nmos_model,pmos_model,2.5e-07, 5e-07,0.05e-6,num=1)\n        self.subcircuit(self.inv_dff)\n\n        self.trans_dff = TransmissionGate(\n            nmos_model=\"NMOS_VTG\",\n            pmos_model=\"PMOS_VTG\"\n        )\n        self.subcircuit(self.trans_dff)\n        # 构建传输门型触发器\n        self.add_dff()",
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
  "ast_dump": "FunctionDef(\n  name='__init__',\n  args=arguments(\n    posonlyargs=[],\n    args=[\n      arg(arg='self'),\n      arg(arg='nmos_model'),\n      arg(arg='pmos_model'),\n      arg(arg='pmos_width'),\n      arg(arg='nmos_width'),\n      arg(arg='length'),\n      arg(arg='w_rc'),\n      arg(arg='pi_res'),\n      arg(arg='pi_cap')],\n    kwonlyargs=[],\n    kw_defaults=[],\n    defaults=[\n      Constant(value='NMOS_VTG'),\n      Constant(value='PMOS_VTG'),\n      Constant(value=5e-07),\n      Constant(value=2.5e-07),\n      Constant(value=5e-08),\n      Constant(value=False),\n      BinOp(\n        left=Constant(value=100),\n        op=MatMult(),\n        right=Name(id='u_Ohm', ctx=Load())),\n      BinOp(\n        left=Constant(value=0.001),\n        op=MatMult(),\n        right=Name(id='u_pF', ctx=Load()))]),\n  body=[\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Call(\n            func=Name(id='super', ctx=Load()),\n            args=[],\n            keywords=[]),\n          attr='__init__',\n          ctx=Load()),\n        args=[\n          Name(id='nmos_model', ctx=Load()),\n          Name(id='pmos_model', ctx=Load()),\n          Name(id='nmos_width', ctx=Load()),\n          Name(id='pmos_width', ctx=Load()),\n          Name(id='length', ctx=Load())],\n        keywords=[\n          keyword(\n            arg='w_rc',\n            value=Name(id='w_rc', ctx=Load())),\n          keyword(\n            arg='pi_res',\n            value=Name(id='pi_res', ctx=Load())),\n          keyword(\n            arg='pi_cap',\n            value=Name(id='pi_cap', ctx=Load()))])),\n    Assign(\n      targets=[\n        Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='inv_dff',\n          ctx=Store())],\n      value=Call(\n        func=Name(id='Pinv', ctx=Load()),\n        args=[\n          Name(id='nmos_model', ctx=Load()),\n          Name(id='pmos_model', ctx=Load()),\n          Constant(value=2.5e-07),\n          Constant(value=5e-07),\n          Constant(value=5e-08)],\n        keywords=[\n          keyword(\n            arg='num',\n            value=Constant(value=1))])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='subcircuit',\n          ctx=Load()),\n        args=[\n          Attribute(\n            value=Name(id='self', ctx=Load()),\n            attr='inv_dff',\n            ctx=Load())],\n        keywords=[])),\n    Assign(\n      targets=[\n        Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='trans_dff',\n          ctx=Store())],\n      value=Call(\n        func=Name(id='TransmissionGate', ctx=Load()),\n        args=[],\n        keywords=[\n          keyword(\n            arg='nmos_model',\n            value=Constant(value='NMOS_VTG')),\n          keyword(\n            arg='pmos_model',\n            value=Constant(value='PMOS_VTG'))])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='subcircuit',\n          ctx=Load()),\n        args=[\n          Attribute(\n            value=Name(id='self', ctx=Load()),\n            attr='trans_dff',\n            ctx=Load())],\n        keywords=[])),\n    Expr(\n      value=Call(\n        func=Attribute(\n          value=Name(id='self', ctx=Load()),\n          attr='add_dff',\n          ctx=Load()),\n        args=[],\n        keywords=[]))],\n  decorator_list=[])"
}
```
