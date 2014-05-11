#!/usr/bin/env python

STYLESHEET = """\
#ue {
	overflow:auto;
}
#score {
	width:50px;
	float:left;
}
#content {
	display:block;
	overflow:hidden;
}
#entry {
	font-weight:bold;
}
#expression {
}
#meaning {
}
#entry_definition {
}
#entry_definition_number {
}
#source {
  font-size:small;
}
h1 {
  font-weight:bold;
}
h2 {
  font-weight:bold;
}
ruby {
  /*display:inline-table;*/
  text-align:center;
  /*white-space:nowrap;*/
  text-indent:0;
  margin:0;
  vertical-align:bottom;
}

ruby>rb,ruby>rbc {
  /*display:table-row-group;*/
}

ruby>rt,ruby>rbc+rtc {
  /*display:table-header-group;*/
  font-size:70%;
  line-height:normal;
  letter-spacing:0;
  -moz-user-select: none;
  -webkit-user-select: none;
  -ms-user-select: none;
}

rp {
  display:none;
}
"""