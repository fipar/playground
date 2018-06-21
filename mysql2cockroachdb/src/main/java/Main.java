
import com.google.code.or.OpenReplicator;
import com.google.code.or.binlog.BinlogEventListener;
import com.google.code.or.binlog.BinlogEventV4;
import com.google.code.or.binlog.BinlogParserContext;
import com.google.code.or.binlog.impl.event.QueryEvent;
import com.google.code.or.binlog.impl.event.TableMapEvent;
import com.google.code.or.binlog.impl.event.WriteRowsEvent;
import com.google.code.or.binlog.impl.event.WriteRowsEventV2;
import com.google.code.or.common.glossary.Column;
import com.google.code.or.common.glossary.Row;
import com.google.code.or.common.util.MySQLConstants;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.TimeUnit;

/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 *
 * @author fipar
 */
public class Main {
    
    private static String currentTable = "";
    
    private static Connection db = null;
    
    private static void handleQueryEvent(BinlogEventV4 event, BinlogParserContext context) {
        System.out.println("Dumping DDL: " + ((QueryEvent)event).getSql());
    }
    
    private static void handleWriteRowsEvent(BinlogEventV4 event, BinlogParserContext context) throws SQLException {
        WriteRowsEvent wre = (WriteRowsEvent) event;
        System.out.println("Dumping WRE into " + currentTable + ": "+wre.toString());
        String sql = "insert into " + currentTable + " values (";
        Iterator<Row> it = wre.getRows().iterator();
        while (it.hasNext()) {
            sql += it.next();
            if (it.hasNext()) {
                sql += ",";
            }
        }
        sql += ")";
        db.createStatement().execute(sql);
        
    }

    private static void handleWriteRowsEventV2(BinlogEventV4 event, BinlogParserContext context) throws SQLException {
        WriteRowsEventV2 wre = (WriteRowsEventV2) event;
        System.out.println("Dumping WREv2: "+wre.toString());
        System.out.println("Dumping WRE into " + currentTable + ": "+wre.toString());
        String sql = "insert into " + currentTable + " values (";
        Iterator<Row> it = wre.getRows().iterator();
        while (it.hasNext()) {
            List<Column> columns = it.next().getColumns();
            for (int i = 0; i < columns.size(); i++) {
                sql += columns.get(i).getValue();
                if (i == columns.size()) {
                    sql += ",";
                }
            }
            sql += ")";
            //TODO: Currently, multiple rows are not supported as this is a POC.
        }
        db.createStatement().execute(sql);        
    }
    
    private static void handleTableMapEvent(BinlogEventV4 event, BinlogParserContext context) {
        TableMapEvent tme = (TableMapEvent) event;
        // TODO: This should return a data type that has the fqtn and the column list with their types
        // so that it can be used to map against a table in ccdb. 
        // Or maybe just use currentTable as now and rely on some form of configuration or a
        // mapping table in ccdb to do that mapping. 
        currentTable = tme.getDatabaseName()+"."+tme.getTableName();
        System.out.println("Dumping TME: "+currentTable+": "+tme.getColumnCount()+" columns, types: "+tme.getColumnTypes());
    }
    
    public static void main(String args[]) throws Exception {
        final OpenReplicator or = new OpenReplicator();
        Class.forName("org.postgresql.Driver");
        db = DriverManager.getConnection("jdbc:postgresql://127.0.0.1:26257/test?sslmode=disable", "replicator", "");
        or.setUser("replicator");
        or.setPassword("replicator");
        or.setHost("localhost");
        or.setPort(3306);
        or.setServerId(2);
        or.setBinlogPosition(4);
        or.setBinlogFileName("telecaster.000001");
        or.setBinlogEventListener(new BinlogEventListener() {
            public void onEvents(BinlogEventV4 event) {
                switch (event.getHeader().getEventType()) {
                    case MySQLConstants.QUERY_EVENT : handleQueryEvent(event, or.getBinlogParser().getContext()); break;
                    case MySQLConstants.WRITE_ROWS_EVENT : 
                        try {
                            handleWriteRowsEvent(event, or.getBinlogParser().getContext());
                        } catch (SQLException sqle) {
                            System.err.println(sqle.getMessage());
                        } break;
                    case MySQLConstants.WRITE_ROWS_EVENT_V2 : 
                        try {
                            handleWriteRowsEventV2(event, or.getBinlogParser().getContext());
                        } catch (SQLException sqle) {
                            System.err.println(sqle.getMessage());
                        }   
                        break;
                    case MySQLConstants.TABLE_MAP_EVENT : handleTableMapEvent(event, or.getBinlogParser().getContext());break;
                    default : System.out.println("Not implemented yet: "+event.toString());
                }
            }
        });
        
        or.start();
        
        System.out.println("press 'q' to stop");
        final BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        for (String line = br.readLine(); line != null; line = br.readLine()) {
            if (line.equals("q")) {
                or.stop(1, TimeUnit.MINUTES);
                break;
            }
        }
    }
    
    
}
