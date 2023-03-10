// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.0
// Date: 20-10-2022

// =======================
// Component control class
// =======================

var $LocalPageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    checkPosition: function(reset) {
    },

    move: function() {
    }
};

var $SidebarDialog = {
    pointer       : null,
    ob            : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    done_action   : null,
    is_active     : null,
    top           : null,
    screen_height : null,

    period_top : 0,

    is_shown      : 1,
    is_activated  : 0,

    init: function() {
        this.pointer = $("#sidebarPointer");
        this.is_active = true;
    },

    activate: function(ob) {
        this.ob = ob;
        this.is_activated = 1;

        if (this.IsDebug)
            alert('$SidebarDialog.activate:'+this.is_active);

        $PageController.hide_lines();

        this.done_action = {'callback':$SidebarDialog.done, 'ob': window.location.toString(), 'force':1};
        //this.done_action = {callback:$onPageLinkSubmit, ob: window.location, force:1};

        $SidebarControl.onNavigatorClick(0, this.done_action);
    },

    clear: function() {
    },

    refreshed: function(x) {
        var self = $SidebarDialog; 

        if (this.IsTrace)
            alert('$SidebarDialog.refreshed');
    },

    resize: function() {
        $PageController.updateLog();
    },

    done: function(link) {
        if (this.IsDebug)
            alert('$SidebarDialog.done:'+link);

        if (!is_empty(link)) {
            $onPageLinkSubmit(link);
        }
        else
            this.resize();
    },
};

var refresh_timeout = 0;
var refresh_timer = null;
var is_forced_refresh = 0;

function refresh_after(timeout) {
    if (is_empty(timeout) || isNaN(timeout))
        return;

    refresh_timeout = timeout * 1000;

    if (IsLog)
        console.log('main.forced_refresh. refresh_timeout:', refresh_timeout);

    if (!is_empty(refresh_timeout) && is_null(refresh_timer) && is_forced_refresh == 0) {
        refresh_timer = setTimeout(function() { forced_refresh(); }, refresh_timeout);
    }
}

function forced_refresh() {
    if (!is_null(refresh_timer)) {
        clearTimeout(refresh_timer);
        refresh_timer = null;
    }

    is_forced_refresh = 1;

    if (IsLog)
        console.log('main.forced_refresh. is_forced_refresh:', is_forced_refresh);

    $Go(default_log_action);
}

var $PageController = {
    callbacks : null,
    container : null,
    tabline   : null,

    group   : null,
    mode    : null,
    timer   : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    period : ['', ''],
    nodes : null,
    boxes : null,
    lines : null,

    show_line_params : null,

    info_node_is_shown : 0,
    context_menu_shown : 0,

    diagram : null,
    contextmenu : null,

    activated_menu : null,

    is_shown_Line : 0,
    shown_Line : null,

    init: function(action, default_action) {
        if (this.IsLog)
            console.log('main.$PageController.init:',action, default_action);

        this.diagram = $("#diagram");
        this.contextmenu = $("#node_context_menu");
    },

    _init_state: function() {

        this.nodes = {};

        this.boxes = {
            '0_01' : ['bgreen', 'bb-bw'],
            '2_20' : ['bred'],
            '3_30' : ['bwhite'],
            '5_50' : ['bblack', 'bb-bw'],
        };

        this.lines = {};
        this.show_line_params = {
            "0_01-1_10": ['m0', null, 0],

            "1_11-1_10": ['m1', null, 5],
            "1_12-1_10": ['m1', 0, 0],
            "1_13-1_10": ['m1', -1, 4],

            "1_10-5_50": ['m2', 90, 0],
            "5_51-5_50": ['m1', 0, 2],

            "2_20-2_21": ['m1', -1, 5],
            "2_20-2_22": ['m1', 0, 0],
            "2_20-2_23": ['m1', 1, 5],

            "3_30-3_31": ['m1', -1, 5],
            "3_30-3_32": ['m1', 0, 0],
            "3_30-3_33": ['m1', 1, 5],

            "4_40-4_41": ['m1', 0, 2],

            "1_10-2_20-1_2": ['m3', -1, 5],
            "1_10-3_30-1_2": ['m3', 0, 2],
            "1_10-4_40-1_2": ['m3', -1, 6],
        };

        if (this.IsLog)
            console.log('main.$PageController._init_state:', this.boxes, this.lines);
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        this._init_state();

        if (action == default_action) {
            ObjectUpdate(args, {
                'refer_id' : SelectedGetItem(LINE, 'id'),
                'forced_refresh' : is_forced_refresh,
                'pagemode' : 'equipment',
            });
        }
        return action;
    },

    action: function(action, args, params) {
        var frm = null;
        if (is_empty(selector) || is_empty(selector.group) || is_empty(tablines))
            return;
        if (['701','702'].indexOf(action) > -1) {
            this.group = selector.group;
            this.mode = selector.mode;
            this.container = selector.tab;
            this.tabline = tablines[this.group];
            frm = $("#"+this.mode+"-form");
            params = this.tabline.get_next_chunk();
            ObjectUpdate(args, {
                'action'   : action,
                'pagemode' : 'equipment',
                'refer_id' : this.tabline.get_id(),
                'group'    : this.group,
                'mode'     : this.mode, 
                'page'     : $("#"+this.group+"-page", frm).val(),
                'per-page' : $("#"+this.group+"-per-page", frm).val(),
                'position' : $("#"+this.group+"-position", frm).val(),
                'params'   : jsonify(params),
                'forced_refresh' : is_forced_refresh,
                //'command': $("#command").val(),
                //'content': $("#refer_content").val(),
            });
        }

        if (this.IsLog)
            console.log('main.$PageController.action', action, selector, args, params);
    },

    sleep: function(callback, timeout) {
        //alert('main.$PageController.sleep:'+timeout);
        this.timer = setTimeout(callback, timeout);
    },

    clear_timeout: function() {
        if (!is_null(this.timer)) {
            clearTimeout(timer);
            this.timer = null;
        }
    },

    activate: function(group, row_id, next_row, chunk) {
        this.clear_timeout();

        if (this.IsLog)
            console.log('main.$PageController.activate.before:', group, row_id, this.container);

        $PageScroller.activate(group, row_id, next_row, chunk);
    },

    updateView: function(action, callbacks, response, props, total) {
        if (this.IsLog)
            console.log('main.$PageController.updateView', action, response, props, total);

        this.group = getattr(props, 'group');
        this.mode = getattr(props, 'mode');

        var refer_id = getattr(props, 'refer_id');
        var row_id = getattr(props, 'row_id');
        var total_html = getattr(props, 'total');
        var chunk = getattr(props, 'chunk');
        var next_row = getattr(props, 'next_row');
        var group = this.group;

        if (this.IsDebug)
            alert('main.$PageController.updateView, action:'+action+', mode:'+this.mode);

        this.callbacks = callbacks;
        mid = '';

        //
        //  Update(refresh) view table content
        //
        set_table = this.callbacks['set_table'];
        switch (action) {
            //
            //  container : target control (table) for update
            //  template : template for table tag of target control
            //  row_class_name : id-prefix for row, not class name! class always: tabline
            //  only_columns : mask['all'|'simple'|1], 
            //        'all' - for every columns, used TEMPLATE_TABLINE_COLUMN
            //        'any' - for every columns, used TEMPLATE_TABLINE_COLUMN_SIMPLE; 
            //        1 - for given ones only 
            //  look 550 of log.default.js
            //  column_class_prefix - prefix for column class name
            //  row_counting - page total control (Total records)
            //  mid : menu id for $ShowMenu, if empty -- no menu
            case default_action:
                break;
            case default_log_action:
                mid = '';
                break;
            default:
                tab_id = group+"-container";
                this.container = $("#tabline-"+group);
                template ='<table class="view-data p100" id="'+tab_id+'" border="1"><thead><tr id="'+group+'-header'+'">';
                row_class_name = 'tabline-'+group;
                only_columns = 1;
                column_class_prefix = 'log-';
                rows_counting = $("#"+group+"-rows-total");
                set_table(this.container, row_class_name, template, only_columns, column_class_prefix, 
                    rows_counting, 
                    total_html,
                    get_chunk_begin(chunk)
                    );
                //this.sleep(function() { $PageController.activate(group, row_id, next_row, chunk); }, default_timeout);
                $PageController.activate(group, row_id, next_row, chunk);
                break;
        }

        return mid;
    },

    all_angles: function (a, b, c) {
        var cosA = (b*b + c*c - a*a) / (2*b*c);
        var cosB = (a*a + c*c - b*b) / (2*a*c);
        var cosC = (a*a + b*b - c*c) / (2*a*b);
    
        A = Math.acos(cosA) * 180 / Math.PI;
        B = Math.acos(cosB) * 180 / Math.PI;
        C = Math.acos(cosC) * 180 / Math.PI;
    
        return [Math.round(A), Math.round(B), Math.round(C)];
    },

    triangle: function(a, b) {
        return int(Math.atan(a/b) * 180 / Math.PI);
    },

    get_line: function(id) {
        var x = id.split('-');
        var x1 = x[0];
        var x2 = x[1];
        var x3 = x.length > 2 ? x[2] : '';

        var line = $("#line_"+id);
        if (!is_exist(line)) {
            var ids = [x2, x1];
            if (!is_empty(x3)) 
                ids.push(x3);
            id = ids.join('-');
            line = $("#line_"+id);
            if (!is_exist(line))
                return [null, id];
        }
        return [line, id];
    },

    set_line(key, params) {
        var x = this.get_line(key);
        var line = x[0];
        var id = x[1];
        if (is_null(line)) {
            if (this.IsLog)
                console.log('main.$PageController.set_line: not exists line:', key, x);
            return;
        }

        var x = id.split('-');
        var x1 = x[0].split('_');
        var x2 = x[1].split('_');
        var id1 = "item_"+x[0];
        var id2 = "item_"+x[1];
        var box1 = $("#"+id1);
        var box2 = $("#"+id2);
        
        var x3 = x.length > 2 ? x[2].split('_') : null;
        var block1 = null, block2 = null;
        var item1 = null, item2 = null;
        var w = 0;

        var b1, b2;
        var i1, i2;

        if (!is_null(x3)) {
            block1 = $("#block_"+x3[0]);
            block2 = $("#block_"+x3[1]);

            if (is_exist(block1) && is_exist(block2)) {
                b1 = $_box_position(block1);
                b2 = $_box_position(block2);

                w = b2.left-(b1.left+b1.width);

                console.log('main.set_line.block.position:', block1.attr('id'), b1, block2.attr('id'), b2, w);
            }

            item1 = $("#item_"+x1[0]);
            item2 = $("#item_"+x2[0]);

            if (is_exist(item1) && is_exist(item2)) {
                i1 = $_box_position(item1);
                i2 = $_box_position(item2);

                w = i2.left -(i1.left+i1.width)-(b1.left+b1.width-(i1.left+i1.width));
            }

            console.log('main.set_line.item.position:', item1.attr('id'), i1, item2.attr('id'), i2, w);
        }

        if (is_exist(box1) && is_exist(box2)) {
            var show_line_params = getattr(this.show_line_params, id);
            var mode = show_line_params[0];

            var p1 = $_box_position(box1);
            var p2 = $_box_position(box2);

            var top  = 0;
            var left = 0;
            var deg = show_line_params[1];
            var p = show_line_params[2] || 0;
            var sclass = params[0] || 'lgreen';
            var x1, x2, width = 0;

            switch (mode) {
            case 'm0':
                top  = p1.top+p1.height+1;
                left = p1.left+p1.width/2;
                x1 = p2.top-(p1.top+p1.height);
                x2 = (p2.left+p2.width/2) - (p1.left+p1.width/2);
                break;
            case 'm1':
                top  = p1.top+p1.height/2;
                left = p1.left+p1.width;
                x1 = (p1.height+p2.height+22)/2;
                x2 = p2.left-(p1.left+p1.width);
                break;
            case 'm2':
                top  = p1.top+p1.height;
                left = p1.left+p1.width/2;
                x1 = p2.top-(p1.top+p1.height);
                x2 = 2;
                break;
            case 'm3':
                top  = p1.top+p1.height/2;
                left = p1.left+p1.width;
                x1 = (p1.top+p1.height/2)-(p2.top+p2.height/2);
                x2 = p2.left-(p1.left+p1.width);
                break;
            case 'm4':
                top  = p1.top+p1.height/2;
                left = p1.left+p1.width;
                x2 = (p1.height+p2.height+22)/2;
                x1 = p2.left-(p1.left+p1.width);
                break;
            }

            x1 -= 2;
            x2 -= 2;

            if ([1, -1, null].indexOf(deg) > -1)
                deg = this.triangle(x1, x2) * (deg != null ? deg : 1);

            width = int(Math.sqrt(Math.pow(x1, 2) + Math.pow(x2, 2)))+p;

            console.log('main.set_line.box.position:', id1, p1, id2, p2, top, left, x1, x2, width, deg);

            line.css({
                top: $_get_css_size(top, 'px'), 
                left: $_get_css_size(left, 'px'),
                width: $_get_css_size(width, 'px'),
                transform: 'rotate('+deg+'deg)',
                'transform-origin': '0% 0%', 
            }).addClass(sclass).show();
        }
    },

    hide_lines: function() {
        for (var key in this.lines) {
            var x = this.get_line(key);
            var line = x[0];
            var id = x[1];

            if (!is_null(line))
                line.hide();
        }
        $("#period").hide();
    },

    set_box: function(id, params) {
        var box = $("#item_"+id);
        var sclass = params[0] || 'bdefault';
        var width_child = params.length > 1 ? params[1] : null;
        if (!is_exist(box))
            return;
        ['bred', 'bgreen', 'bwhite', 'byellow', 'bblack', 'bdefault'].forEach(function(x) {
            box.removeClass(x);
        });

        if (width_child) {
            var x = width_child.split('-');
            box.children('div').each(function(index) {
                $(this).removeClass(x[0]).addClass(x[1]);
            });

        }
        box.addClass(sclass);
    },

    node_info: function(key) {
        node = getattr(this.nodes, key);
        return ' '+getattr(node, 'code')+
            '<div class="node-name">'+getattr(node, 'name')+'</div>'+
            '<div class="node-ip">IP:'+getattr(node, 'ip') +' PORT:'+ getattr(node, 'port')+'</div>';
    },

    show_line: function(ob, with_toggle, mobile) {
        if (!with_toggle) {
            if (this.is_shown_Line == 1) {
                $("#"+this.shown_line).removeClass("thick");
                this.is_shown_Line = 0;
            }
        }

        var css = mobile ? "mobile-thick" : "thick";
        var key = $_get_item_id(ob, -1);

        var x = this.get_line(key);
        var line = x[0];
        var id = x[1];

        //alert(ob.attr('id')+':'+key+':'+id);

        var shown_line = id;

        if (this.is_shown_Line && this.shown_line != shown_line) {
            $("#line_"+this.shown_line).removeClass(css);
            this.is_shown_Line = 0;
        }

        if (this.IsLog)
            console.log('main.$PageController.show_line:', shown_line, line, this.shown_line, this.is_shown_Line);

        if (is_null(line)) 
            return;

        line.toggleClass(css);

        this.shown_line = shown_line;
        this.is_shown_Line = 1 - this.is_shown_Line;
    },

    animate_period: function(box, top, left) {
        var scrolltop = int($(window).scrollTop());
        if (scrolltop < top) {
            box.animate({ top:top+scrolltop, left:left }, 1000, "easeInQuad", function() {});
            this.period_top = this.period_top == 1 ? 0 : 1;
        }
    },

    show_period: function(mode) {
        if (this.IsDebug)
            alert('period:' + this.period);

        var box = $("#period");
        var p = $_box_position(box);
        var width = box.width();
        var g = $_box_position(this.diagram);

        var content = $("div[class~='content']", box).first();
        var html = '<div class="period-info">'+keywords['Active Period']+': '+this.period+'</div>';
        content.html(html);
        var top = int(g.top)-50;
        var left = int(g.left+(g.width/2-p.width/2));

        if (mode == 'over' && is_exist(box)) {
            if (this.period_top == 1)
                top += g.height;

            this.animate_period(box, top, left);
            return;
        } else {
            box.css({ top:$_get_css_size(top), left:$_get_css_size(left) }).show();
            this.period_top = 1;
        }

        if (this.IsLog)
            console.log('show_period:', this.period, g, p);
    },

    info_node_shown: function() {
        return this.info_node_is_shown;
    },

    show_info_node: function(ob, event) {
        var id = ob.attr('id');
        if (this.info_node_is_shown == -1) {
            alert('in progress:'+id);
            return;
        }

        var box = $("#nodeinfo");
        var p = $_box_position(ob);

        if (!is_exist(box)) {
            alert('not exists:'+ id);
            return;
        }

        if (event == 'out') {
            //alert('out:'+id+':'+this.info_node_is_shown+':'+p.top+':'+p.left);
            //box.css({top:0, left:0}).hide();
            box.hide();
            this.info_node_is_shown = 0;
            return;
        }

        if (!is_exist(this.diagram)){
            alert('not exists:diagram');
            return;
        }

        this.info_node_is_shown = -1;

        var p = $_box_position(ob);
        var content = $("div[class~='content']", box).first();

        var g = $_box_position(this.diagram);

        var width = box.width();
        var height = box.height();
        var top = p.top-height-p.height;
        var left = p.left+p.width-width+20;

        if (top+height > g.top+g.height) top = top-height;
        if (left+width > g.left+g.width) left = left - width;

        var info = this.node_info(id);
        var html = '<p>'+keywords['Technical equipment']+''+info+'</p>';
        content.html(html);
        box.css({ top:$_get_css_size(top), left:$_get_css_size(left) }).show();

        this.info_node_is_shown = 1;
    },

    show_contextmenu: function(ob, e, event) {
        if (event == 'close') {
            this.contextmenu.hide();
            this.context_menu_shown = 0;
            return;
        }

        if (!is_exist(ob)) {
            alert('not exists:'+ ob.attr('id'));
            return;
        }

        if (!is_null(e) && this.IsDebug)
            alert('mouse:'+e.pageX+':'+e.pageY);

        if (!is_exist(this.contextmenu)) {
            alert('not exists:contextmenu');
            return;
        }

        var p = $_box_position(this.contextmenu);
        var width = p.width;
        var height = p.height;
        var top = e.pageY+20;
        var left = e.pageX+20;

        var id = ob.attr('id').split('item_')[1];
        var state = getattr(this.boxes, id)[2];
        if (!is_null(state)) {
            var suo = !is_null(state.suo) ? parseInt(state.suo) : -1;
            var ssd = !is_null(state.ssd) ? parseInt(state.ssd) : -1;
        }  else {
            if( this.IsLog )
                console.log('main.menu.$PageController.show_contextmenu:box item is not found:',id, this.boxes);
            return;
        }

        var g = $_box_position(this.diagram);

        //if (top+height > g.top+g.height) top = top-height;
        if (left+width > g.left+g.width) left = left - width;

        if (this.IsLog)
            console.log('main.menu.$PageController.show.contextmenu:', this.contextmenu);

        this.contextmenu.find("a").each(function(index) {
            var item_id = $(this).attr("id");
            $(this).attr("unit", id);

            if (this.IsDebug)
                alert(joinToPrint([item_id, id, suo, ssd]));

            if (item_id.endswith('service')) {
                if (item_id.endswith('start_service') && suo == 2)
                    $(this).removeClass('disabled');
                else if (item_id.endswith('stop_service') && suo == 1)
                    $(this).removeClass('disabled');
                else
                    $(this).addClass('disabled');
            }
        });

        this.contextmenu.css({ top:$_get_css_size(top), left:$_get_css_size(left) }).show();

        this.context_menu_shown = 1;
    },

    contextmenu_activated: function(item) {
        if (!is_exist(item))
            return;
        var menu_id = item.attr('id');
        var unit = item.attr('unit');

        if (this.Isdebug)
            alert('main.$PageController.contextmenu_activated:'+menu_id+':'+ unit);

        this.activated_menu = { menu_id: menu_id, unit:unit };

        $Handle('703', function(x) { $PageController.contextmenu_done(x) }, this.activated_menu );
    },

    contextmenu_done: function(x) {
        var props = getattr(x, 'props');
        var show_notification = getattr(props, 'show_notification', 0);
        var is_done = getattr(props, 'OK');
        var is_error = getattr(props, 'Error');
        var message = getattr(props, 'message', null);
        var is_message = !is_empty(message);

        if (!is_message) {
            message = 'main.$PageController.contextmenu_done: '+'<br>'+
                props.menu_id+'<br>'+' for unit: item_'+props.unit;

            if (is_done && !is_error)
                message = message+'<br>'+' is successfully done';
            else
                message = message+'<br>'+' finished with error!';
        }

        if (is_error)
            $ShowError(message, true, true, false);
        else if (show_notification)
            $NotificationDialog.open(message, 500, 192); // , keywords['Processing info']

    },

    updateLog: function(action, response) {
        /***********
         *    Line definition by key (object):
         *      key: box ID from and box ID to: <from>-<to>:  X_xx-Y_yy
         *    Params (array):
         *      0 -- mode
         *      1 -- deg
         *      2 -- padding
         *      3 -- color class: green|red|black...
         * 
         ***/
        var flash_message = null;
        var with_beep = 0;

        if (!is_empty(response)) {
            var props = getattr(response, 'props');

            this.mode = getattr(response, 'mode');
            this.period = getattr(props, 'period');
            this.nodes = getattr(props, 'nodes');
            this.boxes = getattr(props, 'boxes');
            this.lines = getattr(props, 'lines');

            flash_message = getattr(props, 'flash_message');
            with_beep = getattr(props, 'with_beep');
        }

        if (is_forced_refresh) {
            $AddFlash(flash_message, 'info-flash', 10000, function() { $PageController.updateLog(); });

            is_forced_refresh = 0;

            if (with_beep)
                beep();
        }

        if (this.IsLog)
            console.log('main.$PageController.updateLog:', action, 'boxes:', this.boxes, 'lines:', this.lines);

        if (this.IsDebug)
            alert('main.$PageController.updateLog, action:'+action+', mode:'+this.mode);

        for (var key in this.lines) {
            this.set_line(key, this.lines[key]);
        }

        for (var key in this.boxes) {
            this.set_box(key, this.boxes[key]);
        }

        this.show_period();

        if (!is_forced_refresh && diagram_forced_refresh_timeout > 0) {
            refresh_after(diagram_forced_refresh_timeout);
        }
    },
};

// Size for scroll after activate
var window_scroll = 0;
// Page scroll mode by default
var default_scroll_mode = 'on-place';
