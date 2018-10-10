# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""mock data for testing"""

# data taken from google-cloud-dataflow
DEP_INFO = (
	"""{
	    "PyVCF": 
	    {
	        "installed_version": "0.6.8",
	        "installed_version_time": "2016-03-18 16:19:25+00:00",
	        "latest_version": "0.6.8",
	        "latest_version_time": "2016-03-18 16:19:25+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.362146+00:00"
	    },
	    "PyYAML": 
	    {
	        "installed_version": "3.13",
	        "installed_version_time": "2018-07-05 22:53:15+00:00",
	        "latest_version": "3.13",
	        "latest_version_time": "2018-07-05 22:53:15+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.434491+00:00"
	    },
	    "apache-beam": 
	    {
	        "installed_version": "2.7.0",
	        "installed_version_time": "2018-06-26 05:28:08+00:00",
	        "latest_version": "2.6.0",
	        "latest_version_time": "2018-08-08 18:15:31+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:08:58.798679+00:00"
	    },
	    "avro": 
	    {
	        "installed_version": "1.8.2",
	        "installed_version_time": "2017-05-20 15:56:15+00:00",
	        "latest_version": "1.8.2",
	        "latest_version_time": "2017-05-20 15:56:15+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:58.872872+00:00"
	    },
	    "cachetools": 
	    {
	        "installed_version": "2.1.0",
	        "installed_version_time": "2018-05-12 16:26:31+00:00",
	        "latest_version": "2.1.0",
	        "latest_version_time": "2018-05-12 16:26:31+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:58.935337+00:00"
	    },
	    "certifi": 
	    {
	        "installed_version": "2018.8.13",
	        "installed_version_time": "2018-08-13 07:10:37+00:00",
	        "latest_version": "2018.8.13",
	        "latest_version_time": "2018-08-13 07:10:37+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:58.999951+00:00"
	    },
	    "chardet": 
	    {
	        "installed_version": "3.0.4",
	        "installed_version_time": "2017-06-08 14:34:33+00:00",
	        "latest_version": "3.0.4",
	        "latest_version_time": "2017-06-08 14:34:33+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.059407+00:00"
	    },
	    "crcmod": 
	    {
	        "installed_version": "1.7",
	        "installed_version_time": "2010-06-27 14:35:29+00:00",
	        "latest_version": "1.7",
	        "latest_version_time": "2010-06-27 14:35:29+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.132582+00:00"
	    },
	    "dill": 
	    {
	        "installed_version": "0.2.6",
	        "installed_version_time": "2017-02-01 19:15:09+00:00",
	        "latest_version": "0.2.8.2",
	        "latest_version_time": "2018-06-22 22:12:44+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:08:59.193692+00:00"
	    },
	    "docopt": 
	    {
	        "installed_version": "0.6.2",
	        "installed_version_time": "2014-06-16 11:18:57+00:00",
	        "latest_version": "0.6.2",
	        "latest_version_time": "2014-06-16 11:18:57+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.277869+00:00"
	    },
	    "enum34": 
	    {
	        "installed_version": "1.1.6",
	        "installed_version_time": "2016-05-16 03:31:13+00:00",
	        "latest_version": "1.1.6",
	        "latest_version_time": "2016-05-16 03:31:13+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.342615+00:00"
	    },
	    "fasteners": 
	    {
	        "installed_version": "0.14.1",
	        "installed_version_time": "2015-11-13 06:47:45+00:00",
	        "latest_version": "0.14.1",
	        "latest_version_time": "2015-11-13 06:47:45+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.407208+00:00"
	    },
	    "funcsigs": 
	    {
	        "installed_version": "1.0.2",
	        "installed_version_time": "2016-04-25 22:22:05+00:00",
	        "latest_version": "1.0.2",
	        "latest_version_time": "2016-04-25 22:22:05+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.490506+00:00"
	    },
	    "future": 
	    {
	        "installed_version": "0.16.0",
	        "installed_version_time": "2016-10-27 20:07:22+00:00",
	        "latest_version": "0.16.0",
	        "latest_version_time": "2016-10-27 20:07:22+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.554068+00:00"
	    },
	    "futures": 
	    {
	        "installed_version": "3.2.0",
	        "installed_version_time": "2017-11-30 23:22:35+00:00",
	        "latest_version": "3.2.0",
	        "latest_version_time": "2017-11-30 23:22:35+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.615168+00:00"
	    },
	    "gapic-google-cloud-pubsub-v1": 
	    {
	        "installed_version": "0.15.4",
	        "installed_version_time": "2017-04-14 17:47:55+00:00",
	        "latest_version": "0.15.4",
	        "latest_version_time": "2017-04-14 17:47:55+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.733030+00:00"
	    },
	    "google-apitools": 
	    {
	        "installed_version": "0.5.20",
	        "installed_version_time": "2017-12-18 22:52:40+00:00",
	        "latest_version": "0.5.23",
	        "latest_version_time": "2018-04-24 15:57:55+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:08:59.804865+00:00"
	    },
	    "google-auth": 
	    {
	        "installed_version": "1.5.1",
	        "installed_version_time": "2018-07-31 23:24:08+00:00",
	        "latest_version": "1.5.1",
	        "latest_version_time": "2018-07-31 23:24:08+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.868660+00:00"
	    },
	    "google-auth-httplib2": 
	    {
	        "installed_version": "0.0.3",
	        "installed_version_time": "2017-11-14 17:37:59+00:00",
	        "latest_version": "0.0.3",
	        "latest_version_time": "2017-11-14 17:37:59+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:08:59.939852+00:00"
	    },
	    "google-cloud-bigquery": 
	    {
	        "installed_version": "0.25.0",
	        "installed_version_time": "2017-06-26 23:46:02+00:00",
	        "latest_version": "1.5.0",
	        "latest_version_time": "2018-08-02 22:48:21+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:00.035277+00:00"
	    },
	    "google-cloud-core": 
	    {
	        "installed_version": "0.25.0",
	        "installed_version_time": "2017-06-26 22:03:32+00:00",
	        "latest_version": "0.28.1",
	        "latest_version_time": "2018-02-28 20:01:50+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:00.110586+00:00"
	    },
	    "google-cloud-dataflow": 
	    {
	        "installed_version": "2.5.0",
	        "installed_version_time": "2018-06-27 17:22:15+00:00",
	        "latest_version": "2.5.0",
	        "latest_version_time": "2018-06-27 17:22:15+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.303731+00:00"
	    },
	    "google-cloud-pubsub": 
	    {
	        "installed_version": "0.26.0",
	        "installed_version_time": "2017-06-26 23:46:11+00:00",
	        "latest_version": "0.37.0",
	        "latest_version_time": "2018-08-14 17:47:22+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:00.375273+00:00"
	    },
	    "google-gax": 
	    {
	        "installed_version": "0.15.16",
	        "installed_version_time": "2017-11-10 21:25:36+00:00",
	        "latest_version": "0.16.0",
	        "latest_version_time": "2018-02-28 21:10:07+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:00.437938+00:00"
	    },
	    "googleapis-common-protos": 
	    {
	        "installed_version": "1.5.3",
	        "installed_version_time": "2017-09-26 21:16:44+00:00",
	        "latest_version": "1.5.3",
	        "latest_version_time": "2017-09-26 21:16:44+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.497815+00:00"
	    },
	    "googledatastore": 
	    {
	        "installed_version": "7.0.1",
	        "installed_version_time": "2017-04-10 16:32:21+00:00",
	        "latest_version": "7.0.1",
	        "latest_version_time": "2017-04-10 16:32:21+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.653841+00:00"
	    },
	    "grpc-google-iam-v1": 
	    {
	        "installed_version": "0.11.4",
	        "installed_version_time": "2017-09-22 15:23:23+00:00",
	        "latest_version": "0.11.4",
	        "latest_version_time": "2017-09-22 15:23:23+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.708233+00:00"
	    },
	    "grpcio": 
	    {
	        "installed_version": "1.14.1",
	        "installed_version_time": "2018-08-08 19:31:37+00:00",
	        "latest_version": "1.14.1",
	        "latest_version_time": "2018-08-08 19:31:37+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.850325+00:00"
	    },
	    "hdfs": 
	    {
	        "installed_version": "2.1.0",
	        "installed_version_time": "2017-09-08 03:57:21+00:00",
	        "latest_version": "2.1.0",
	        "latest_version_time": "2017-09-08 03:57:21+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:00.941405+00:00"
	    },
	    "httplib2": 
	    {
	        "installed_version": "0.9.2",
	        "installed_version_time": "2015-09-28 13:55:48+00:00",
	        "latest_version": "0.11.3",
	        "latest_version_time": "2018-03-30 02:29:15+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:01.090439+00:00"
	    },
	    "idna": 
	    {
	        "installed_version": "2.7",
	        "installed_version_time": "2018-06-11 02:52:19+00:00",
	        "latest_version": "2.7",
	        "latest_version_time": "2018-06-11 02:52:19+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.159959+00:00"
	    },
	    "mock": 
	    {
	        "installed_version": "2.0.0",
	        "installed_version_time": "2016-04-06 01:38:18+00:00",
	        "latest_version": "2.0.0",
	        "latest_version_time": "2016-04-06 01:38:18+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.222772+00:00"
	    },
	    "monotonic": 
	    {
	        "installed_version": "1.5",
	        "installed_version_time": "2018-05-03 20:55:31+00:00",
	        "latest_version": "1.5",
	        "latest_version_time": "2018-05-03 20:55:31+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.311531+00:00"
	    },
	    "oauth2client": 
	    {
	        "installed_version": "4.1.2",
	        "installed_version_time": "2017-06-29 22:06:33+00:00",
	        "latest_version": "4.1.2",
	        "latest_version_time": "2017-06-29 22:06:33+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.384495+00:00"
	    },
	    "pbr": 
	    {
	        "installed_version": "4.2.0",
	        "installed_version_time": "2018-07-23 22:26:49+00:00",
	        "latest_version": "4.2.0",
	        "latest_version_time": "2018-07-23 22:26:49+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.483006+00:00"
	    },
	    "pip": 
	    {
	        "installed_version": "10.0.1",
	        "installed_version_time": "2018-04-19 18:56:05+00:00",
	        "latest_version": "18.0",
	        "latest_version_time": "2018-07-22 07:53:50+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:01.559689+00:00"
	    },
	    "ply": 
	    {
	        "installed_version": "3.8",
	        "installed_version_time": "2015-10-02 18:15:50+00:00",
	        "latest_version": "3.11",
	        "latest_version_time": "2018-02-15 19:01:27+00:00",
	        "is_latest": false,
	        "current_time": "2018-08-16 01:09:01.609361+00:00"
	    },
	    "proto-google-cloud-datastore-v1": 
	    {
	        "installed_version": "0.90.4",
	        "installed_version_time": "2017-04-28 21:22:56+00:00",
	        "latest_version": "0.90.4",
	        "latest_version_time": "2017-04-28 21:22:56+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.727899+00:00"
	    },
	    "proto-google-cloud-pubsub-v1": 
	    {
	        "installed_version": "0.15.4",
	        "installed_version_time": "2017-04-14 17:47:42+00:00",
	        "latest_version": "0.15.4",
	        "latest_version_time": "2017-04-14 17:47:42+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:01.922813+00:00"
	    },
	    "protobuf": 
	    {
	        "installed_version": "3.6.1",
	        "installed_version_time": "2018-08-13 22:47:09+00:00",
	        "latest_version": "3.6.1",
	        "latest_version_time": "2018-08-13 22:47:09+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.005171+00:00"
	    },
	    "pyasn1": 
	    {
	        "installed_version": "0.4.4",
	        "installed_version_time": "2018-07-26 07:43:55+00:00",
	        "latest_version": "0.4.4",
	        "latest_version_time": "2018-07-26 07:43:55+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.091667+00:00"
	    },
	    "pyasn1-modules": 
	    {
	        "installed_version": "0.2.2",
	        "installed_version_time": "2018-06-28 08:01:55+00:00",
	        "latest_version": "0.2.2",
	        "latest_version_time": "2018-06-28 08:01:55+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.172666+00:00"
	    },
	    "pytz": 
	    {
	        "installed_version": "2018.5",
	        "installed_version_time": "2018-06-29 06:53:04+00:00",
	        "latest_version": "2018.5",
	        "latest_version_time": "2018-06-29 06:53:04+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.276061+00:00"
	    },
	    "requests": 
	    {
	        "installed_version": "2.19.1",
	        "installed_version_time": "2018-06-14 13:40:38+00:00",
	        "latest_version": "2.19.1",
	        "latest_version_time": "2018-06-14 13:40:38+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.525582+00:00"
	    },
	    "rsa": 
	    {
	        "installed_version": "3.4.2",
	        "installed_version_time": "2016-03-29 13:16:23+00:00",
	        "latest_version": "3.4.2",
	        "latest_version_time": "2016-03-29 13:16:23+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.589273+00:00"
	    },
	    "setuptools": 
	    {
	        "installed_version": "40.0.0",
	        "installed_version_time": "2018-07-09 04:23:03+00:00",
	        "latest_version": "40.0.0",
	        "latest_version_time": "2018-07-09 04:23:03+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.705405+00:00"
	    },
	    "six": 
	    {
	        "installed_version": "1.11.0",
	        "installed_version_time": "2017-09-17 18:46:53+00:00",
	        "latest_version": "1.11.0",
	        "latest_version_time": "2017-09-17 18:46:53+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.767901+00:00"
	    },
	    "typing": 
	    {
	        "installed_version": "3.6.4",
	        "installed_version_time": "2018-01-25 00:54:56+00:00",
	        "latest_version": "3.6.4",
	        "latest_version_time": "2018-01-25 00:54:56+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.820013+00:00"
	    },
	    "urllib3": 
	    {
	        "installed_version": "1.23",
	        "installed_version_time": "2018-06-05 03:25:49+00:00",
	        "latest_version": "1.23",
	        "latest_version_time": "2018-06-05 03:25:49+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.894411+00:00"
	    },
	    "wheel": 
	    {
	        "installed_version": "0.31.1",
	        "installed_version_time": "2018-05-13 17:28:23+00:00",
	        "latest_version": "0.31.1",
	        "latest_version_time": "2018-05-13 17:28:23+00:00",
	        "is_latest": true,
	        "current_time": "2018-08-16 01:09:02.966368+00:00"
	    }
	}"""
)
