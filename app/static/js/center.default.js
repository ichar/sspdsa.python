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

        this.done_action = {'callback':$SidebarDialog.done, 'ob': window.location.toString(), 'force':1};

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
        console.log('center.forced_refresh. refresh_timeout:', refresh_timeout);

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
        console.log('center.forced_refresh. is_forced_refresh:', is_forced_refresh);

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

    period : null,

    show_line_params : null,

    info_node_is_shown : 0,
    context_menu_shown : 0,

    mainbox : null,
    contextmenu : null,

    activated_menu : null,

    is_shown_Line : 0,
    shown_Line : null,

    init: function(action, default_action) {
        if (this.IsLog)
            console.log('center.$PageController.init:',action, default_action);

        this.mainbox = $("#mainlines");
        this.contextmenu = $("#node_context_menu");
    },

    _init_state: function() {
        if (this.IsLog)
            console.log('center.$PageController._init_state:');

        this.show_period(null);
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        this._init_state();

        if (action == default_action) {
            ObjectUpdate(args, {
                'refer_id' : SelectedGetItem(LINE, 'id'),
                'forced_refresh' : is_forced_refresh,
                'pagemode' : 'center',
            });
        }
        return action;
    },

    action: function(action, args, params) {
        var frm = null;
        if (is_empty(selector) || is_empty(selector.group) || is_empty(tablines))
            return;
        if (['801','802'].indexOf(action) > -1) {
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
            console.log('center.$PageController.action', action, selector, args, params);
    },

    sleep: function(callback, timeout) {
        //alert('center.$PageController.sleep:'+timeout);
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
            console.log('center.$PageController.activate.before:', group, row_id, this.container);

        $PageScroller.activate(group, row_id, next_row, chunk);
    },

    updateView: function(action, callbacks, response, props, total) {
        if (this.IsLog)
            console.log('center.$PageController.updateView', action, response, props, total);

        this.group = getattr(props, 'group');
        this.mode = getattr(props, 'mode');

        var refer_id = getattr(props, 'refer_id');
        var row_id = getattr(props, 'row_id');
        var total_html = getattr(props, 'total');
        var chunk = getattr(props, 'chunk');
        var next_row = getattr(props, 'next_row');
        var group = this.group;

        if (this.IsDebug)
            alert('center.$PageController.updateView, action:'+action+', mode:'+this.mode);

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

    node_info: function(key) {
        node = getattr(this.nodes, key);
        return ' '+getattr(node, 'code')+
            '<div class="node-name">'+getattr(node, 'name')+'</div>'+
            '<div class="node-ip">IP:'+getattr(node, 'ip') +' PORT:'+ getattr(node, 'port')+'</div>';
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
        var p = $_box_position(box, 'period');
        var width = box.width();

        this.mainbox = $("#mainlines");
        var g = $_box_position(this.mainbox, 'mainlines');

        if (!is_null(this.period)) {
            var content = $("div[class~='content']", box).first();
            var html = '<div class="period-info">'+keywords['Active Period']+': '+this.period+'</div>';
            content.html(html);
        }
        var top = int(g.top)-80;
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
                console.log('center.menu.$PageController.show_contextmenu:box item is not found:',id, this.boxes);
            return;
        }

        var g = $_box_position(this.mainbox);

        //if (top+height > g.top+g.height) top = top-height;
        if (left+width > g.left+g.width) left = left - width;

        if (this.IsLog)
            console.log('center.menu.$PageController.show.contextmenu:', this.contextmenu);

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
            alert('center.$PageController.contextmenu_activated:'+menu_id+':'+ unit);

        this.activated_menu = { menu_id: menu_id, unit:unit };

        $Handle('803', function(x) { $PageController.contextmenu_done(x) }, this.activated_menu );
    },

    contextmenu_done: function(x) {
        var props = getattr(x, 'props');
        var show_notification = getattr(props, 'show_notification', 0);
        var is_done = getattr(props, 'OK');
        var is_error = getattr(props, 'Error');
        var message = getattr(props, 'message', null);
        var is_message = !is_empty(message);

        if (!is_message) {
            message = 'center.$PageController.contextmenu_done: '+'<br>'+
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
            console.log('center.$PageController.updateLog:', action);

        this.show_period(null);

        if (!is_forced_refresh && center_forced_refresh_timeout > 0) {
            refresh_after(center_forced_refresh_timeout);
        }
    },
};

// Size for scroll after activate
var window_scroll = 0;
// Page scroll mode by default
var default_scroll_mode = 'on-place';

