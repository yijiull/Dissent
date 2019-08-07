#ifndef DISSENT_APPLICATIONS_COMMAND_LINE_H_GUARD
#define DISSENT_APPLICATIONS_COMMAND_LINE_H_GUARD

#include <QList>
#include <QObject>
#include <QTime>
#include <QSharedPointer>
#include <QSocketNotifier>
#include <QTextStream>

#include "ConsoleSink.hpp"

namespace Dissent {
namespace Applications {
  class Node;

  /**
   * Allows for Asynchronous access to the commandline for input and output
   * purposes.  Useful for console applications.
   */
  class CommandLine : public ConsoleSink {
    Q_OBJECT

    public:
      /**
       * Constructor
       * @param nodes the set of nodes running in this process
       */
      explicit CommandLine(const QList<QSharedPointer<Node> > &nodes);

      virtual ~CommandLine();

      /**
       * Start the command line services
       */
      void Start(int id);

      /**
       * A sink input to print data to the console in a pretty way
       * @param from the sender of the data
       * @param data incoming data
       */
      virtual void HandleData(const QSharedPointer<ISender> &from,
          const QByteArray &data);

    public slots:
      /**
       * Stop the commmand line services
       */
      void Stop();

    private slots:
      /**
       * Called when there is input on stdin
       */
      void Read();

    signals:
      void mysignal();

    protected:
      QTime m_time;
      int session_id;
      int time_sum;
      QString m_msg;
      const QList<QSharedPointer<Node> > &m_nodes;
      int m_current_node;
      int m_cnt;
      bool m_running;
      QTextStream m_qtin;
  };
}
}

#endif
