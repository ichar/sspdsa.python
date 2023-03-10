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

var $PageController = {
    callbacks : null,
    container : null,
    tabline   : null,

    timer : null,

    IsDebug : 0, IsTrace : 0, IsLog : 1,

    init: function(action, default_action) {
        if (this.IsTrace)
            alert('references.$PageController.init: '+action+':'+default_action);
    },

    _init_state: function() {
        if (this.IsLog)
            console.log('references.$PageController._init_state:');
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        if (action == default_action) {
            ObjectUpdate(args, {
                'refer_id' : SelectedGetItem(LINE, 'id'),
            });
        }
    },

    action: function(action, args, params) {
        if (this.IsLog)
            console.log('references.$PageController.action.before', action, selector, tablines, args, params);

        var frm = null;
        if (is_empty(selector) || is_empty(selector.group) || is_empty(tablines))
            return;
        if (['502', '503'].indexOf(action) > -1) {
            this.group = selector.group;
            this.mode = selector.mode;
            this.container = selector.tab;
            this.tabline = tablines[this.group];
            frm = $("#"+this.mode+"-form");
            console.log('tabline:', this.tabline);
            params = this.tabline.get_next_chunk();
            ObjectUpdate(args, {
                'action'   : action,
                'refer_id' : tablines[this.group].get_id(),
                'group'    : this.group,
                'mode'     : this.mode, 
                'page'     : $("#"+this.group+"-page", frm).val(),
                'per-page' : $("#"+this.group+"-per-page", frm).val(),
                'position' : $("#"+this.group+"-position", frm).val(),
                'params'   : jsonify(params),
                //'command': $("#command").val(),
                //'content': $("#refer_content").val(),
            });
        }
        if (this.IsLog)
            console.log('references.$PageController.action.after', action, args, params);
    },

    sleep: function(callback, timeout) {
        //alert('references.$PageController.sleep:'+timeout);
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
            console.log('references.$PageController.activate.before:', group, row_id, this.container);

        $PageScroller.activate(group, row_id, next_row, chunk);
    },

    updateView: function(action, callbacks, response, props, total) {
        if (this.IsLog)
            console.log('references.$PageController.updateView', action, response, props, total);

        this.group = getattr(props, 'group');
        this.mode = getattr(props, 'mode');

        var refer_id = getattr(props, 'refer_id');
        var row_id = getattr(props, 'row_id');
        var total_html = getattr(props, 'total');
        var chunk = getattr(props, 'chunk');
        var next_row = getattr(props, 'next_row');
        var group = this.group;

        if (this.IsDebug)
            alert('references.$PageController.updateView, action:'+action+', mode:'+mode);

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
            case default_log_action:
                //set_table($("#line-table"), 'tabline');
                mid = '';
                break;
            default:
                tab_id = group+"-container";
                this.container = $("#tabline-"+group);
                template ='<table class="view-data p100" id="'+tab_id+'" border="1"><thead><tr>';
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

    contextmenu_activated: function(item){
        if (!is_exist(item))
            return;
        var menu_id = item.attr('id');

        if (this.Isdebug)
            alert('references.$PageController.contextmenu_activated:'+menu_id);

        this.activated_menu = { menu_id: menu_id };

        $Handle('504', function(x) { $PageController.contextmenu_done(x) }, this.activated_menu );
    },

    contextmenu_done: function(x) {
        var props = getattr(x, 'props');
        var show_notification = getattr(props, 'show_notification', 0);
        var is_done = getattr(props, 'OK');
        var is_error = getattr(props, 'Error');
        var message = getattr(props, 'message', null);
        var is_message = !is_empty(message);

        if (!is_message) {
            message = 'references.$PageController.contextmenu_done: '+'<br>'+
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
    }
};

// Current review container ID
var selected_review_id = 'subline_review';
// Size for scroll after activate
var window_scroll = 0;
// Page scroll mode by default
var default_scroll_mode = 'on-place';

var $PageLoader = {
    container   : null,
    actions     : {'change':'502'},

    IsDebug : 0, IsDeepDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    id          : null,
    command     : '',
    mode        : '',
    box         : null,
    
    scroll_mode : '',
    scroll_top  : 0,
    top         : 0,
    height      : 0,

    is_error    : false,
    is_shown    : false,
    is_locked   : false,

    line        : {'id' : null, 'state_is_open' : -1},

    init: function() {
        this.container = $("#"+selected_review_id);

        if (this.IsTrace)
            alert('references.$PageLoader.init:'+$LineSelector.get_id()+':'+$LineSelector.get_current().get(0).outerHTML);

        this.line['id'] = null;

        is_full_container = 1;

        this.scroll_top = $(window).scrollTop();
    },

    reset: function() {
        this._show();
        this._reset();

        this.scroll_top = $(window).scrollTop();
    },

    scroll: function() {
        if (window_scroll != null) {
            $(window).scrollTop(window_scroll || 0);

            window_scroll = null;

            $_show_page(0);
            return;
        }

        var current_top = $LineSelector.get_current().position().top;

        if (this.IsDebug)
            alert(['references.$PageLoader.scroll', this.scroll_mode, this.line['state_is_open'], this.scroll_top, this.height, int(this.top), int(current_top)].join(':'));

        if (this.top == 0 || this.height == 0 || this.top > current_top)
            return;

        var offset = 5;

        switch (this.scroll_mode) {
            case 'top':
                $(window).scrollTop(current_top - offset);
                break;
            case 'on-place':
                if (this.line['state_is_open'] != 0) {
                    var x = this.scroll_top - this.height - offset;
                    if (x > 0)
                        $(window).scrollTop(x);
                }
                break;
            default:
                break;
        }

        this.scroll_mode = '';
    },

    remove_current: function() {
        if (!is_null(this.container)) {
            try {
                this.top = this.container.position().top;
                this.height = this.container.height();
            } 
            catch(e) {
                if (this.IsTrace) 
                    alert('references.$PageLoader.remove_current: Error');
                this.height = 0;
            }
            this.container.remove();
        }
    },

    _lock: function() {
        this.is_locked = true;
    },

    _unlock: function() {
        this.is_locked = false;
    },

    locked: function() {
        return this.is_locked;
    },

    _before: function(ob, command) {
        should_be_updated = false;
        selected_menu_action = default_log_action;

        this.box = ob;
        this.command = command;

        if (!is_null(this.command)) {
            if (this.command.toLowerCase().search('add') > -1)
                this.id = null;
            else
                this.id = $TablineSelector.get_id();
        }

        $InProgress(ob, 1);

        this.is_error = false;
    },

    _reset: function() {
        this.action = null;
        this.id = null;
        this.mode = null;
        this.box = null;
    },

    _hide: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = true;
    },

    _show: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = false;
    },

    _clean: function() {
    },

    set: function(x) {
        var data = x['data']['data'][0];

        if (this.IsLog)
            console.log('references.$PageLoader.set, mode:', this.mode, data, x);

        switch (this.mode) {
        case 'param':
            $("#param").val(data['ParamID']);
            $("#new_param").val('');
            //$("#param_value").val(data['Value']);

            check_param(data['Value'], 0);
            break;
        }

        this._hide();
        this._after();
    },

    get: function(action, ob, command) {
        this.action = action;
        this.mode = command.split('_')[1].toLowerCase();

        this._before(ob, command);

        var params = {'command':command, 'id':this.id};

        $Handle(this.action, function(x) { $PageLoader.set(x); }, params);
    },

    cancel: function(action, ob, command) {
        this._clean();
        this._show();
        this._after();
    },

    check: function(x) {
        var errors = x['errors'];

        if (this.IsLog)
            console.log('$PageLoader.check, errors:', errors.length);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;

            this._show();
        }
    },

    handle: function(x) {
        this._reset();
        this._after();
    },

    handle_change: function(ob, command) {
        if (this.IsLog)
            console.log('$PageLoader.handle_change', ob, command);

        action = this.actions.change;

        params = Object.assign(default_params, {
             'content': $("#refer_content").val(),
             'command': command,
        });

        this._before(ob, command);

        $Handle(action, function(x) { $PageLoader.refresh_after_action(x); }, params);
    },

    handle_refresh: function(action, ob, command) {
        this.action = action;
        this.mode = 'refresh';

        var params = {'command':command};

        $Handle(this.action, function(x) { $PageLoader.refresh_after_action(x); }, params);
    },

    select_item: function(action, ob, command) {
    },

    is_activated: function() {
        return this.line['state_is_open'] == -1 ? true : false;
    },

    activate: function(ob) {
        var line_id = $_get_item_id(ob);

        if (this.IsDeepDebug)
            alert(['references.$PageLoader.activate', 
                this.line['id'], 
                line_id, 
                this.container.attr('id'), ob.position().top].join(':')
                );

        if (this.line['id'] == line_id) {
            if (this.line['state_is_open'] == 1) {
                this.container.addClass('closed');
                this.line['state_is_open'] = 0;
            }
            else if (this.line['state_is_open'] == 0) {
                this.container.removeClass('closed');
                this.line['state_is_open'] = 1;
            }
            return;
        }

        this.scroll_mode = default_scroll_mode;

        this._lock();

        $LineSelector.onRefresh(ob);
    },

    refresh_line: function(response, line) {
        if (this.IsLog)
            console.log('$PageLoader.refresh_line', response);

        var data = getattr(response, 'data', null);
        var columns = getattr(response, 'columns', null);
        var props = getattr(response, 'props', null);

        if (is_null(line))
            line = $LineSelector.get_current();

        $PageController.updateLog(data, props);

        this._after();
    },

    refresh_status: function(response) {
    },

    refresh_after_action: function(response) {
        if (this.IsTrace)
            alert('references.$PageLoader.refresh_after_action');

        if (this.IsLog)
            console.log('$PageLoader.refresh_after_action', response);

        if (!is_null(response)) {
            var action = getattr(response, 'action', default_action);
            var props = getattr(response, 'props', null);
            var total = parseInt(getattr(response, 'total', '0'));
            var status = getattr(response, 'status', null);
            var path = getattr(response, 'path', null);;

            selected_menu_action = action;

            if (action == default_action) {
                $updateLineData(action, response, props, total, status, path);
            }
            else if (action == default_log_action) {
                $updateSublineData(action, response, props, total, status, path);
            }

            this.refresh_line(response);
        }
    },

    refresh: function(response) {
        /***
         *  Called by default_handler, action:default_log_action
         */
        if (this.IsTrace)
            alert('references.$PageLoader.refresh');

        this.reset();

        var current_action = default_action;

        this.init();

        this.remove_current();

        var columns = response['columns'];
        var colspan = columns.length || 10;

        this.refresh_after_action(response);

        if (this.IsLog)
            console.log('$PageLoader.refresh, selected_data_menu_id:', selected_data_menu_id);

        if (!is_full_container)
            this.scroll();

        this._unlock();

        this._after();

        this._register();

        if (!search_is_empty())
            return;
    },

    _after: function() {
        selected_menu_action = default_log_action;
        isCallback = false;
    }
};

