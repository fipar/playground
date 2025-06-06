package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
	"unsafe"

	"github.com/google/gopacket"
	"github.com/google/gopacket/examples/util"
	_ "github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"gopkg.in/mgo.v2/bson"
)

var iface = flag.String("i", "eth0", "Interface to read packets from")
var fname = flag.String("r", "", "Filename to read from, overrides -i")
var snaplen = flag.Int("s", 65536, "Snap length (number of bytes max to read per packet")
var tstype = flag.String("timestamp_type", "", "Type of timestamps to use")
var promisc = flag.Bool("promisc", true, "Set promiscuous mode")
var verbose = 2

// next code all copied from facebookgo/dvara

// OpCode allows identifying the type of operation:
//
// http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#request-opcodes
type OpCode int32

// all data in the MongoDB wire protocol is little-endian.
// all the read/write functions below are little-endian.
func getInt32(b []byte, pos int) int32 {
	return (int32(b[pos+0])) |
		(int32(b[pos+1]) << 8) |
		(int32(b[pos+2]) << 16) |
		(int32(b[pos+3]) << 24)
}

func setInt32(b []byte, pos int, i int32) {
	b[pos] = byte(i)
	b[pos+1] = byte(i >> 8)
	b[pos+2] = byte(i >> 16)
	b[pos+3] = byte(i >> 24)
}

// The full set of known request op codes:
// http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#request-opcodes
const (
	OpReply       = OpCode(1)
	OpMessage     = OpCode(1000)
	OpUpdate      = OpCode(2001)
	OpInsert      = OpCode(2002)
	Reserved      = OpCode(2003)
	OpQuery       = OpCode(2004)
	OpGetMore     = OpCode(2005)
	OpDelete      = OpCode(2006)
	OpKillCursors = OpCode(2007)
)

type messageHeader struct {
	// MessageLength is the total message size, including this header
	MessageLength int32
	// RequestID is the identifier for this miessage
	RequestID int32
	// ResponseTo is the RequestID of the message being responded to. used in DB responses
	ResponseTo int32
	// OpCode is the request type, see consts above.
	OpCode OpCode
}

// FromWire reads the wirebytes into this object
func (m *messageHeader) FromWire(b []byte) {
	m.MessageLength = getInt32(b, 0)
	m.RequestID = getInt32(b, 4)
	m.ResponseTo = getInt32(b, 8)
	m.OpCode = OpCode(getInt32(b, 12))
}

/*

From http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/

OP_UPDATE

struct OP_UPDATE {
    MsgHeader header;             // standard message header
    int32     ZERO;               // 0 - reserved for future use
    cstring   fullCollectionName; // "dbname.collectionname"
    int32     flags;              // bit vector. see below
    document  selector;           // the query to select the document
    document  update;             // specification of the update to perform
}

OP_INSERT

struct {
    MsgHeader header;             // standard message header
    int32     flags;              // bit vector - see below
    cstring   fullCollectionName; // "dbname.collectionname"
    document* documents;          // one or more documents to insert into the collection
}

OP_QUERY

struct OP_QUERY {
    MsgHeader header;                 // standard message header
    int32     flags;                  // bit vector of query options.  See below for details.
    cstring   fullCollectionName ;    // "dbname.collectionname"
    int32     numberToSkip;           // number of documents to skip
    int32     numberToReturn;         // number of documents to return
                                      //  in the first OP_REPLY batch
    document  query;                  // query object.  See below for details.
  [ document  returnFieldsSelector; ] // Optional. Selector indicating the fields
                                      //  to return.  See below for details.
}

so document is at offset 16 + 4 + N + 4 + 4

*/

// this map will store the start time for all requests. K:RequestId, v:StartTime
var startTimes = make(map[int32]time.Time)

// this map will store the query text (as I reconstructed/inferred it) for all requests. K:RequestId, v:Query
var queries = make(map[int32]string)

// my functions now

/*
struct OP_UPDATE {
    MsgHeader header;             // standard message header
    int32     ZERO;               // 0 - reserved for future use
    cstring   fullCollectionName; // "dbname.collectionname"
    int32     flags;              // bit vector. see below
    document  selector;           // the query to select the document
    document  update;             // specification of the update to perform
}

*/

func processUpdatePayload(data []byte, header messageHeader) (output string) {
	sub := data[20:]
	current := sub[0]
	docStartsAt := 0
	for i := 0; current != 0; i++ {
		current = sub[i]
		docStartsAt = i
	}
	collectionName := sub[0:docStartsAt]
	docStartsAt += 5 // ++ and then skip flags since I don't care about them right now
	mybson := sub[docStartsAt+8:]
	docEndsAt := mybson[0]
	bdoc := mybson[:docEndsAt]
	json := make(map[string]interface{})
	bson.Unmarshal(bdoc, json)
	if verbose > 2 {
		fmt.Print("Unmarshalled selector json: ")
		fmt.Println(json)
	}
	output = fmt.Sprintf("%v.update({", string(collectionName[:]))
	output += recurseJsonMap(json)
	output += "},{"
	if verbose > 2 {
		fmt.Print("Selector: ")
		fmt.Print("mybson bytes: ")
		fmt.Println(mybson)
		fmt.Print("Document bytes:")
		fmt.Println(bdoc)
		fmt.Print("Document size in bytes: ")
		fmt.Println(unsafe.Sizeof(bdoc))
	}
	docEndsAt = sub[docEndsAt : docEndsAt+1][0]
	mybson = sub[docEndsAt+1:]
	bdoc = mybson[:docEndsAt]
	json = make(map[string]interface{})
	bson.Unmarshal(bdoc, json)
	if verbose > 2 {
		fmt.Print("Unmarshalled updater json: ")
		fmt.Println(json)
	}
	output += recurseJsonMap(json)
	output += "});\n"
	return output
}

func processInsertPayload(data []byte, header messageHeader) (output string) {
	sub := data[20:]
	current := sub[0]
	docStartsAt := 0
	for i := 0; current != 0; i++ {
		current = sub[i]
		docStartsAt = i
	}
	collectionName := sub[0:docStartsAt]
	mybson := sub[docStartsAt+8:]
	docEndsAt := mybson[0]
	bdoc := mybson[:docEndsAt]
	json := make(map[string]interface{})
	bson.Unmarshal(bdoc, json)
	if verbose > 2 {
		fmt.Print("Unmarshalled selector json: ")
		fmt.Println(json)
	}
	output = fmt.Sprintf("%v.insert({", string(collectionName[:]))
	output += recurseJsonMap(json)
	output += "});\n"
	return output
}

func processQueryPayload(data []byte, header messageHeader) (output string) {
	sub := data[20:]
	current := sub[0]
	docStartsAt := 0
	for i := 0; current != 0; i++ {
		current = sub[i]
		docStartsAt = i
	}
	collectionName := sub[0:docStartsAt]
	docStartsAt++
	if verbose > 2 {
		fmt.Print("Raw data: ")
		fmt.Println(data)
		fmt.Printf("Querying collection %v\n", string(collectionName[:]))
	}
	if string(collectionName[len(collectionName)-4:len(collectionName)]) == "$cmd" {
		output = fmt.Sprintf("db.runCommand({")
	} else {
		output = fmt.Sprintf("%v.find({", string(collectionName[:]))
	}
	mybson := sub[docStartsAt+8:]
	docEndsAt := mybson[0]
	bdoc := mybson[:docEndsAt]
	json := make(map[string]interface{})
	bson.Unmarshal(bdoc, json)
	if verbose > 2 {
		fmt.Print("Unmarshalled json: ")
		fmt.Println(json)
	}
	if len(json) == 0 {
		output = fmt.Sprintf("%v.find();\n", string(collectionName[:]))
	} else {
		output += recurseJsonMap(json)
		output += "});\n"
	}
	if verbose > 2 {
		fmt.Print("mybson bytes: ")
		fmt.Println(mybson)
		fmt.Print("Document bytes:")
		fmt.Println(bdoc)
		fmt.Print("Document size in bytes: ")
		fmt.Println(unsafe.Sizeof(bdoc))
	}
	return output
}

func recurseJsonMap(json map[string]interface{}) (output string) {
	i := 0
	output = ""
	for k, v := range json {
		i++
		comma := ", "
		if i == len(json) {
			comma = ""
		}
		switch extracted_v := v.(type) {
		case string:
			output += fmt.Sprintf("%v:%v%v", k, extracted_v, comma)
		case int, int32, int64:
			output += fmt.Sprintf("%v:%v%v", k, extracted_v.(int), comma)
		case float64:
			output += fmt.Sprintf("%v:%v%v", k, float64(extracted_v), comma)
		case map[string]interface{}:
			output += fmt.Sprintf("%v:{%v}%v", k, recurseJsonMap(extracted_v), comma)
		default:
			output += fmt.Sprintf("%v:%T%v", k, extracted_v, comma)
		}

	}
	return output
}

func processReplyPayload(data []byte, header messageHeader) (output float64) {
	var elapsed float64 = 0
	start, ok := startTimes[header.RequestID]
	if ok {
		elapsed = time.Since(start).Seconds()
		delete(startTimes, header.RequestID)
	}
	return elapsed
}

/*
# Time: 150402 14:02:44
# User@Host: [fernandoipar] @ localhost []
# Thread_id: 13  Schema:   Last_errno: 0  Killed: 0
# Query_time: 0.000052  Lock_time: 0.000000  Rows_sent: 1  Rows_examined: 0  Rows_affected: 0  Rows_read: 0
# Bytes_sent: 90
SET timestamp=1427994164;
db.sample.find({a:"test", b:"another test"});

Mon Jan 2 15:04:05 -0700 MST 2006


*/

func getSlowQueryLogHeader(elapsed float64, sent int) (output string) {
	now := time.Now().Format("060102 15:04:05")
	output = fmt.Sprintf("# Time: %v\n", now)
	output += "# User@Host: [undefined] @ undefined []\n"
	output += "# Thread_id: 1 Schema: Last_errno: 0 Killed: 0\n"
	output += fmt.Sprintf("# Query_time: %f Lock_time: 0 Rows_sent: 1 Rows_examined: 1 Rows_affected: 1 Rows_read: 1\n", elapsed)
	output += fmt.Sprintf("# Bytes_sent: %v\n", sent)
	output += fmt.Sprintf("SET timestamp=%v;\n", time.Now().Unix())
	return output
}

func dump(src gopacket.PacketDataSource) {
	var dec gopacket.Decoder
	var ok bool
	if dec, ok = gopacket.DecodersByLayerName["Ethernet"]; !ok {
		log.Fatalln("No decoder named", "Ethernet")
	}
	source := gopacket.NewPacketSource(src, dec)
	//source.Lazy = *lazy
	source.NoCopy = true
	for packet := range source.Packets() {
		//fmt.Println(packet.ApplicationLayer().Payload())
		al := packet.ApplicationLayer()
		if al != nil {
			/*
				json := make(map[string]interface{})
				//var mbson []bson.M
				bson.Unmarshal(al.Payload(), json)
				for k, v := range json {
					fmt.Println(k);
					fmt.Println(v);
				}
			*/
			payload := al.Payload()
			// IMPORTANT
			// This code is unsafe. It performs no check and will fail miserably if the packet is
			// not a mongo packet. Pass the proper 'port N' filter to pcap when invoking the program
			var header messageHeader
			header.MessageLength = getInt32(payload, 0)
			header.RequestID = getInt32(payload, 4)
			header.ResponseTo = getInt32(payload, 8)
			header.OpCode = OpCode(getInt32(payload, 12))
			startTimes[header.RequestID] = time.Now()
			fmt.Println("OpCode: ", header.OpCode)
			if verbose > 2 {
				fmt.Println("Captured packet")
				fmt.Printf("Captured packet (OpCode: %v)\n", header.OpCode)
			}
			switch header.OpCode {
			case OpQuery:
				queries[header.RequestID] = processQueryPayload(payload, header)
			case OpReply:
				elapsed := processReplyPayload(payload, header)
				fmt.Print(getSlowQueryLogHeader(elapsed, len(payload)))
				query, ok := queries[header.ResponseTo]
				if ok {
					fmt.Print(query)
					delete(queries, header.ResponseTo)
				} else {
					fmt.Print("   Orphaned reply ...")
				}
			case OpUpdate:
				queries[header.RequestID] = processUpdatePayload(payload, header)
			case OpInsert:
				queries[header.RequestID] = processInsertPayload(payload, header)
			default:
				fmt.Println("Unimplemented Opcode ", header.OpCode)
			}
		}
	}
}

// this main() is heavily inspired by / is a frankensteined version of https://github.com/google/gopacket/blob/master/examples/pcapdump/main.go

func main() {
	defer util.Run()()
	var handle *pcap.Handle
	var err error
	flag.Parse()
	if *fname != "" {
		if handle, err = pcap.OpenOffline(*fname); err != nil {
			log.Fatal("PCAP OpenOffline error:", err)
		}
	} else {
		// This is a little complicated because we want to allow all possible options
		// for creating the packet capture handle... instead of all this you can
		// just call pcap.OpenLive if you want a simple handle.
		inactive, err := pcap.NewInactiveHandle(*iface)
		if err != nil {
			log.Fatal("could not create: %v", err)
		}
		defer inactive.CleanUp()
		if err = inactive.SetSnapLen(*snaplen); err != nil {
			log.Fatal("could not set snap length: %v", err)
		} else if err = inactive.SetPromisc(*promisc); err != nil {
			log.Fatal("could not set promisc mode: %v", err)
		} else if err = inactive.SetTimeout(time.Second); err != nil {
			log.Fatal("could not set timeout: %v", err)
		}
		if *tstype != "" {
			if t, err := pcap.TimestampSourceFromString(*tstype); err != nil {
				log.Fatalf("Supported timestamp types: %v", inactive.SupportedTimestamps())
			} else if err := inactive.SetTimestampSource(t); err != nil {
				log.Fatalf("Supported timestamp types: %v", inactive.SupportedTimestamps())
			}
		}
		if handle, err = inactive.Activate(); err != nil {
			log.Fatal("PCAP Activate error:", err)
		}
		defer handle.Close()
		if len(flag.Args()) > 0 {
			bpffilter := strings.Join(flag.Args(), " ")
			fmt.Fprintf(os.Stderr, "Using BPF filter %q\n", bpffilter)
			if err = handle.SetBPFFilter(bpffilter); err != nil {
				log.Fatal("BPF filter error:", err)
			}
		}
	}
	for {
		dump(handle)
	}
}
