// ***************************************************
// APPLICATION PAGE DECLARATION: /spologger.default.js
// HELPER FUNCTION CONTROLS MANAGER
// ---------------------------------------------------
// Version: 2.0
// Date: 01-10-2022

// =======================
// Component control class
// =======================

var $LocalPageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,
    is_trace  : 0,

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
    is_trace  : 0,

    init: function(action, default_action) {
        if (this.is_trace)
            alert('spologger.$PageController.init: '+action+':'+default_action);
    },

    _init_state: function() {
        if (this.IsLog)
            console.log('spologger.$PageController._init_state:');
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        if (action == default_action) {
            ObjectUpdate(args, {
                'log_id' : SelectedGetItem(LINE, 'id'),
                'batch_id' : '',  //$("#batchtype").val()
                'batch_status' : '',  //$("#batchstatus").val()
            });
        }
        return action;
    },

    action: function(action, args, params) {
        if (action > default_action) {

            ObjectUpdate(args, {
                'action' : action,
                'log_id' : SelectedGetItem(LINE, 'id'),
                'batch_id' :  '', //SelectedGetItem(SUBLINE, 'id')
            });
        }
    },

    updateLog: function(action, response) {

    },

    updateView: function(action, callbacks, response, props, total) {
        if (this.IsLog)
            console.log('spologger.$PageController.updateView', action, response, props, total);

        var group = getattr(props, 'group');
        var mode = getattr(props, 'mode');
        var refer_id = getattr(props, 'refer_id');
        var row_id = getattr(props, 'row_id');

        if (this.IsDebug)
            alert('spologger.$PageController.updateView, action:'+action+', mode:'+mode);

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
        }

        return mid;
    }
};
