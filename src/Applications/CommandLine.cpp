#include <unistd.h>
#include <qcoreapplication.h>

#include "CommandLine.hpp"
#include "Node.hpp"

namespace Dissent {
namespace Applications {
  CommandLine::CommandLine(const QList<QSharedPointer<Node> > &nodes) :
    m_nodes(nodes),
    m_current_node(0),
    m_cnt(0),
    m_running(false),
    m_qtin(stdin, QIODevice::ReadOnly)
  {
  }

  CommandLine::~CommandLine()
  {
    Stop();
  }

  void CommandLine::Start(int id)
  {
    if(m_running) {
      return;
    }

    m_running = true;
    session_id = id;
      for(int i = 0; i < 132; i++){
          m_msg += (char)(id + 65);
      }
      m_qtout<<m_msg<<endl;

    QObject::connect(this, SIGNAL(mysignal()), this, SLOT(Read()));
    emit mysignal();
  }

  void CommandLine::Stop()
  {
    if(!m_running) {
      return;
    }

    m_running = false;

    QObject::disconnect(this, SIGNAL(mysignal()), this, SLOT(Read()));

    m_qtout << endl << "Goodbye" << endl << endl;
  }


  void CommandLine::HandleData(const QSharedPointer<ISender> &from,
      const QByteArray &data)
  {
      auto res = m_time.elapsed();
      m_qtout<<res<<endl;
      QString msg = QString::fromUtf8(data.data());
      m_qtout << endl << "Incoming data: " << from->ToString() << " " << msg << endl;
      m_cnt++;
      time_sum += res;
      if(m_cnt == 10)
      {
        m_qtout << "session id: " << session_id << "  time: " << time_sum / m_cnt << endl;
        m_cnt = 0;
        time_sum = 0;
      }
      emit mysignal();
  }

  void CommandLine::Read()
  {
    if(session_id >= 0){
        m_time.restart();
        m_nodes[m_current_node]->GetSession()->Send(m_msg.toUtf8());
    }
  }
}
}
